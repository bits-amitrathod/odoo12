# -*- coding: utf-8 -*-
import pytz
import time
from datetime import date, datetime
import csv
import pysftp

from odoo import api, fields, models, _

# forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')

HEAD = """ISA^00^          ^00^          ^ZZ^{sender_id}^ZZ^{receiver_id}^{YYMMHH}^{HHMM}^U^00401^{x_interchange}^0^T^|~
GS^IN^{sender_id}^{accounting_id}^{current_date}^{HHMM}^335^X^004010~
ST^810^3350001~
BIG^{invoice_date}^{invoice_name}^^{po_number}^^^DI~
REF^OQ^{order_ref}~
N1^BT^^{fields_92_bt}^{bill_to_id}~
N1^ST^^91^{store_num}~
N1^RI^^{fields_91_ri}^{x_store_id}~
N2^{add1}~
N3^{add2}~
N4^{city}^{state}^{zip}~
N1^VN^^{fields_92_vn}^{remit_to}~
ITD^ZZ^3^^^^20051009^30~"""

LINE = """
IT1^{line_num}^{qty_done}^{uom}^{unit_price}^^VC^{product_desc}^{in_value_field}^{buyer_part_num}~"""

FOOT = """
TDS^{amount_total}~
TXI^ST^{tax_total}~
CTT^{invoice_lines_num}~
SE^{number_of_segments}^3350001~
GE^1^335~
IEA^1^{x_interchange}~"""

# EDI Block
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
BIL_FIELDS = ['TRANSACTION ID', 'ACCOUNTING ID', 'INVOICE #', 'INVOICE DATE',
              'PO #', 'PO DATE', 'DEPT #', 'BILL OF LADING', 'CARRIER PRO #',
              'SCAC', 'SHIP VIA', 'SHIP TO NAME', 'SHIP TO ADDRESS 1',
              'SHIP TO ADDRESS 2', 'SHIP TO CITY', 'SHIP TO STATE',
              'SHIP TO ZIP CODE', 'SHIP TO COUNTRY', 'STORE #', 'BILL TO NAME',
              'BILL TO ADDRESS 1', 'BILL TO ADDRESS 2', 'BILL TO CITY',
              'BILL TO STATE', 'BILL TO ZIP CODE', 'BILL TO COUNTRY',
              'BILL TO CODE', 'SHIP DATE', 'TERMS DESCRIPTION', 'NET DAYS DUE',
              'DISCOUNT DAYS DUE', 'DISCOUNT PERCENT', 'NOTE', 'WEIGHT',
              'TOTAL CASES SHIPPED', 'TAX AMOUNT', 'CHARGE AMOUNT 1',
              'CHARGE AMOUNT 2', 'ALLOWANCE PERCENT 1', 'ALLOWANCE AMOUNT 1',
              'ALLOWANCE PERCENT 2', 'ALLOWANCE AMOUNT 2', 'LINE #',
              'VENDOR PART #', 'BUYER PART #', 'UPC #', 'DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'UNIT PRICE', 'QUANTITY ORDERED',
              'PACK SIZE', '# OF INNER PACKS', 'ITEM ALLOWANCE PERCENT',
              'ITEM ALLOWANCE AMOUNT', 'TRANSACTION TYPE', 'SHIP TO TYPE']


class AccountMove(models.Model):
    _inherit = ['account.move']

    x_edi_ship_to_type = fields.Selection([('DC', 'Warehouse Number'), ('SN', 'Store Number')], string='Ship To Type')
    x_edi_transaction_type = fields.Char('EDI Transaction Type')
    x_studio_edi_reference = fields.Char('EDI Reference', copy=False)
    x_edi_accounting_id = fields.Char('Accounting ID', copy=False)
    x_edi_store_number = fields.Char('Store number', copy=False)
    invn_sent = fields.Boolean('Invoice Notification Sent?', copy=False)
    edi_log_id = fields.Many2one('setu.edi.log', copy=False)
    sale_order_of = fields.Selection([('true', 'Truecommerce'), ('ghx', 'GHX')])

    def get_terms_values(self, sale):
        discount_days = net_days = discount_percent = 'null'
        term = self.invoice_payment_term_id
        if term.line_ids and len(term.line_ids) > 1:
            if 'percent' in term.line_ids.mapped('value'):
                net_days = self.env['account.payment.term.line'].browse(
                    sorted(term.line_ids.filtered(lambda line: line.value == 'balance').ids, reverse=True))[0].days
                discount_days = term.line_ids.filtered(lambda line: line.value == 'percent').days
                discount_percent = 100 - float(
                    term.line_ids.filtered(lambda line: line.value == 'percent').value_amount)
        else:
            if term and term.line_ids:
                net_days = term.line_ids.filtered(lambda line: line.value == 'balance')[0].days
            discount_days = False
            discount_percent = False

        return net_days, discount_days, discount_percent

    def prepare_log_line_vals(self, line, order, pick, charge_amount, allowance_amount):
        user_tz = pytz.timezone(self.env.user.tz or 'utc')

        po_line = line.mapped('sale_line_ids')[0].po_log_line_id if line.mapped('sale_line_ids') and \
                                                                    line.mapped('sale_line_ids')[0] else False
        buyer_part = False
        if line.sale_line_ids and line.sale_line_ids.mapped('po_log_line_id'):

            buyer_part = line.sale_line_ids and line.sale_line_ids[0].po_log_line_id and line.sale_line_ids[0].po_log_line_id.buyers_part_num or ''
        ship_date = order.picking_ids.filtered(
            lambda pick: pick.picking_type_id.code == 'outgoing' and pick.state == 'done') and str(
            order.picking_ids.filtered(lambda pick: pick.picking_type_id.code == 'outgoing' and pick.state == 'done')[
                0].date_done.astimezone(user_tz).date()) or ''
        log_line_vals = {
            'po_date': str(order.date_order.astimezone(user_tz).date()),
            'ship_date': ship_date,
            'ship_to_name': line.move_id.partner_shipping_id.id,
            'bill_to_name': line.move_id.partner_id.id,
            'vendor_part': line.product_id.default_code,
            'buyer_part': buyer_part,
            'upc': line.product_id.barcode,
            'description': line.product_id.description_sale or line.product_id.name,
            'qty_shipped': line.quantity,
            'qty_ordered': sum([x.product_uom_qty for x in line.sale_line_ids]),
            'uom': line.product_uom_id.name,
            'unit_price': line.price_unit,
            'amount_by_group': line.move_id.amount_tax,
            'scac': pick and pick.x_scac_kuebix or '',
            'carrier_tracking_ref': pick and pick.carrier_tracking_ref or '',
            'ship_via': pick.shipping_service or '',
            'carrier_id': False,
            'x_edi_transaction_type': line.move_id.x_edi_transaction_type,
            'x_edi_ship_to_type': line.move_id.x_edi_ship_to_type
        }
        if self.sale_order_of == 'true':
            ap1 = ap2 = aa1 = aa2 = False
            if po_line:
                ap1 = po_line.allowance_percent_1
                ap2 = po_line.allowance_percent_2
                # aa1 = po_line.allowance_amount_1
                aa2 = po_line.allowance_amount_2
            charge = ''
            allowance = ''
            bill_to_code = line.sale_line_ids[0].po_log_line_id.bill_to_code if line.sale_line_ids and \
                                                                                line.sale_line_ids[
                                                                                    0] and line.sale_line_ids[
                                                                                    0].po_log_line_id and \
                                                                                line.sale_line_ids[
                                                                                    0].po_log_line_id.bill_to_code else False
            if charge_amount and line.product_id.product_tmpl_id.edi_charge_amount:
                charge = charge_amount
            if allowance_amount and line.product_id.product_tmpl_id.edi_allowance_amount:
                allowance = allowance_amount
            net_days, discount_days, discount_percent = self.get_terms_values(order)
            log_line_vals.update({
                'net_days_due': net_days,
                'discount_percent': discount_percent,
                'discount_days_due': discount_days,
                'allowance_percent_1': ap1,
                'allowance_percent_2': ap2,
                'allowance_amount_1': allowance,
                'allowance_amount_2': aa2,
                'charge_amount_1': charge,
                'charge_amount_2': 'null',
                'bill_to_code': bill_to_code,
                'invoice_payment_term_id': line.move_id.invoice_payment_term_id.id,
            })
        return log_line_vals

    def create_invn_log(self):
        """
        Will create invoice notification log.
        @return:
        """
        charge_amount = False
        allowance_amount = False
        order = self.env['sale.order'].search([('name', '=',
                                                self.invoice_origin)])  # list(set(self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')))
        order = order and order[0]

        if not order:
            order_list = self.invoice_line_ids and self.invoice_line_ids.sale_line_ids and self.invoice_line_ids.sale_line_ids.mapped(
                'order_id')
            order = order_list[0]
            if not order:
                return self.env['setu.edi.log']
        pick = order.picking_ids.filtered(
            lambda pick: pick.picking_type_id.code == 'outgoing' and pick.state in ['done', 'waiting', 'confirmed',
                                                                                    'assigned']) or False
        pick = pick and pick[0] or False
        log_id = self.env['setu.edi.log'].create({
            'document_type': '810',
            'invoice_id': self.id,
            'po_number': order.client_order_ref,
            'type': 'export',
            'sale_id': order.id
        })
        lines_with_edi_charge_amt = self.invoice_line_ids.filtered(
            lambda inv: inv.product_id.product_tmpl_id.edi_charge_amount)

        if lines_with_edi_charge_amt:
            charge_amount = sum([x.price_subtotal for x in lines_with_edi_charge_amt])

        lines_with_edi_allowance_amt = self.invoice_line_ids.filtered(
            lambda inv: inv.product_id.product_tmpl_id.edi_allowance_amount)
        if lines_with_edi_allowance_amt:
            allowance_amount = sum([x.price_subtotal for x in lines_with_edi_allowance_amt])

        for line in self.invoice_line_ids:
            log_line_vals = self.prepare_log_line_vals(line, order, pick, charge_amount, allowance_amount)
            log_id.write({
                'edi_810_log_lines': [(0, 0, log_line_vals)]
            })
        if self.sale_order_of == 'ghx':
            log_id.x_hdr_ref1 = order and order.customer_po_ref and order.customer_po_ref.x_hdr_ref1

        return log_id

    def export_invn(self, sftp, log_id):
        """
        Will upload .csv file on sftp server of 810 file.
        @param sftp: sftp instance.
        @param log_id:
        @return:
        """
        user_tz = pytz.timezone(self.env.user.tz or 'utc')
        order = self.env['sale.order'].sudo().search(
            [('name', '=', str(self.invoice_origin))], limit=1)
        # BEGINS CREATE EDI INVOICE
        sftp_conf = self.env['setu.sftp'].search(
            [('company_id', '=', self.company_id.id), ('instance_of', '=', self.sale_order_of),
             ('instance_active', '=', True)])

        ftpdpath = sftp_conf['ftp_invack_dpath']
        file_name = '/tmp/' + str(DOC_PREFIX_BIL) + '_' + \
                    str(order.client_order_ref) + '_' + \
                    str(order.partner_id.name) + '.csv'
        with open(file_name, 'w') as file_pointer:
            if sftp_conf.instance_of == 'true':
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=BIL_FIELDS)
                writer.writeheader()
                line_num = 0
                for row in log_id.edi_810_log_lines:
                    line_num += 1
                    ship_to_type_selection = row.fields_get().get('x_edi_ship_to_type').get('selection')
                    ship_to_type = [a[1] for a in ship_to_type_selection if a[0] == row.x_edi_ship_to_type]
                    ship_to_type_val = False
                    if ship_to_type and ship_to_type[0]:
                        ship_to_type_val = ship_to_type[0]
                    cvs_rows.append({
                        'TRANSACTION ID': DOC_PREFIX_BIL,
                        'ACCOUNTING ID': row.x_edi_accounting_id,
                        'INVOICE #': row.invoice_name,
                        'INVOICE DATE': str(row.invoice_date),
                        'PO #': log_id.po_number,
                        'PO DATE': row.po_date,
                        'DEPT #': 'null',
                        'BILL OF LADING': row.bill_of_landing,
                        'CARRIER PRO #': row.carrier_tracking_ref,
                        'SCAC': row.scac,
                        'SHIP VIA': row.ship_via,
                        'SHIP TO NAME': row.ship_to_name.name,
                        'SHIP TO ADDRESS 1':
                            row.ship_to_address_1 or 'null',
                        'SHIP TO ADDRESS 2':
                            row.ship_to_address_2 or 'null',
                        'SHIP TO CITY':
                            row.ship_to_city or 'null',
                        'SHIP TO STATE':
                            row.ship_to_state or 'null',
                        'SHIP TO ZIP CODE':
                            row.ship_to_zip or 'null',
                        'SHIP TO COUNTRY':
                            row.ship_to_country or 'null',
                        'STORE #': row.x_edi_store_number,
                        'BILL TO NAME': row.bill_to_name.name,
                        'BILL TO ADDRESS 1':
                            row.bill_to_address_1 or 'null',
                        'BILL TO ADDRESS 2':
                            row.bill_to_address_2 or 'null',
                        'BILL TO CITY':
                            row.bill_to_city or 'null',
                        'BILL TO STATE':
                            row.bill_to_state or 'null',
                        'BILL TO ZIP CODE':
                            row.bill_to_zip or 'null',
                        'BILL TO COUNTRY':
                            row.bill_to_country or 'null',
                        'BILL TO CODE': 'null',
                        'SHIP DATE': row.ship_date,
                        'TERMS DESCRIPTION':
                            row.invoice_payment_term_id.name or 'null',
                        'NET DAYS DUE': row.net_days_due or 'null',
                        'DISCOUNT DAYS DUE': row.discount_days_due or 'null',
                        'DISCOUNT PERCENT': row.discount_percent or 'null',
                        'NOTE': order.note and order.note or '',
                        'WEIGHT': 'null',
                        'TOTAL CASES SHIPPED': 'null',
                        'TAX AMOUNT':
                            row.amount_by_group or 0.0,
                        'CHARGE AMOUNT 1': row.charge_amount_1,
                        'CHARGE AMOUNT 2': row.charge_amount_2,
                        'ALLOWANCE PERCENT 1': row.allowance_percent_1,
                        'ALLOWANCE AMOUNT 1': row.allowance_amount_1,
                        'ALLOWANCE PERCENT 2': row.allowance_percent_2,
                        'ALLOWANCE AMOUNT 2': row.allowance_amount_2,
                        'LINE #': line_num,
                        'VENDOR PART #': row.vendor_part or '',
                        'BUYER PART #': row.buyer_part or '',
                        'UPC #': row.upc,
                        'DESCRIPTION': row.description,
                        'QUANTITY SHIPPED': row.qty_shipped or 0.0,
                        'UOM': row.uom,
                        'UNIT PRICE': row.unit_price or 0.0,
                        'QUANTITY ORDERED': row.qty_ordered,
                        'PACK SIZE': 'null',
                        '# OF INNER PACKS': 'null',
                        'ITEM ALLOWANCE PERCENT': 'null',
                        'ITEM ALLOWANCE AMOUNT': 'null',
                        'TRANSACTION TYPE': row.x_edi_transaction_type,
                        'SHIP TO TYPE': row.x_edi_ship_to_type
                    })
                writer.writerows(cvs_rows)
            else:
                interchange = sftp_conf.update_interchange_number()
                current_date = str(date.today()).replace('-', '')
                current_time = str(datetime.now().time()).replace(':', '')[0:4]
                invoice_date = str(self.invoice_date).replace('-', '')

                head = HEAD.format(
                    add1=self.partner_id and self.partner_id.street or '',
                    add2=self.partner_id and self.partner_id.street2 or '',
                    city=self.partner_id and self.partner_id.city or '',
                    state=self.partner_id and self.partner_id.state_id and self.partner_id.state_id.name or '',
                    zip=self.partner_id and self.partner_id.zip,
                    sender_id=sftp_conf.sender_id and sftp_conf.sender_id.ljust(15) or '',
                    receiver_id=sftp_conf.receiver_id and sftp_conf.receiver_id.ljust(15) or '',
                    YYMMHH=current_date[2:] or '',
                    HHMM=current_time or '',
                    x_interchange=interchange or '',
                    accounting_id=self.partner_id.x_edi_accounting_id or '',
                    current_date=current_date or '',
                    invoice_date=invoice_date or '',
                    invoice_name=self.name or '',
                    po_number=order and order.customer_po_ref and order.customer_po_ref.po_number or '',
                    order_ref=order.x_hdr_ref1 or '',
                    bill_to_id=order.partner_id.x_billtoid or '',
                    store_num=self.x_edi_store_number or '',
                    x_store_id=order.partner_id.x_storeid or '',
                    remit_to=order.partner_id.remit_to or '',
                    fields_92_bt='92' if order.partner_id.x_billtoid else '',
                    fields_91_ri='91' if order.partner_id.x_storeid else '',
                    fields_92_vn='92' if order.partner_id.remit_to else ''
                )
                seq = 0
                lines = """"""
                for line in self.invoice_line_ids:
                    seq += 1
                    po_log_line_id = line.sale_line_ids[0].po_log_line_id if line.sale_line_ids and line.sale_line_ids[
                        0] and line.sale_line_ids[0].po_log_line_id else False
                    buyer_part = line.sale_line_ids and line.sale_line_ids[0].po_log_line_id and line.sale_line_ids[0].po_log_line_id.buyers_part_num or ''
                    line_num = '0000' + str(seq)
                    lines += LINE.format(
                        line_num=po_log_line_id.line_num if po_log_line_id else line_num[-4:] or '',
                        qty_done=int(line.quantity) or '',
                        uom=line.sale_line_ids and line.sale_line_ids[0].po_log_line_id and line.sale_line_ids[0].po_log_line_id.uom or line.product_uom_id.name or '',
                        unit_price=line.price_unit or '',
                        product_desc=line.product_id.description_sale or line.product_id.name or '',
                        buyer_part_num=buyer_part or '',
                        in_value_field='IN' if buyer_part else ''
                    )
                segments = seq + 10

                foot = FOOT.format(
                    amount_total=int(self.amount_total * 100) or '',
                    tax_total=line.move_id.amount_tax or '',
                    invoice_lines_num=seq or '',
                    number_of_segments=segments or '',
                    x_interchange=interchange or ''
                )
                res = head + lines + foot
                file_pointer.write(res)
        if sftp:
            sftp.cwd(ftpdpath)
            if self.sale_order_of == 'true':
                sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_BIL) + '_' + str(order.client_order_ref) + '_' \
                         + str(order.partner_id.name) + '_' + str(self.name).replace('/', '_') + '.csv')
            else:
                date_time = str(datetime.now()).replace('-', '').replace(':', '')[0:13].replace(' ', '')
                sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_BIL) + '_' + str(self.name).replace('/', '_') + '_' \
                         + date_time + '.txt')
            return True
        return False

    def create_and_export_invn(self):
        """
        Main method to create Invoice notification log and export.

        @return:
        """
        log_ids = self.env['setu.edi.log']
        sftp = False
        for invoice in self:

            sftp_conf = invoice.env['setu.sftp'].search(
                [('company_id', '=', invoice.company_id.id), ('instance_of', '=', invoice.sale_order_of),
                 ('instance_active', '=', True)])
            if sftp_conf:
                sftp, status = sftp_conf.test_connection()
                if sftp:
                    log = invoice.create_invn_log()
                    invoice.edi_log_id = log
                    log_ids |= log
                    for log_id in log_ids:
                        res = invoice.export_invn(sftp, log_id)
                        if res:
                            invoice.invn_sent = True
                            log.status = 'success'
                        else:
                            log.status = 'fail'
                else:
                    log_id = self.env['setu.edi.log'].create({
                        'po_number': invoice.id,
                        'type': 'export',
                        'document_type': '810',
                        'status': 'fail',
                        'exception': status,
                        'invoice_id': invoice.id
                    })
                    log_ids |= log_id
            if sftp:
                sftp.close()
        return log_ids

    def action_post(self):
        """
        This Function is used create Invoice(810-880) file if the entry is
        related to SO. and call invoice action post function that execute
        default behaviour.
        :return:
        """
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.partner_id.edi_810 and not rec.invn_sent:
                rec.create_and_export_invn()
        return res


class AccMoveRev(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res = super(AccMoveRev, self).reverse_moves()
        moves = self.move_ids
        sale_obj = self.env['sale.order'].sudo()
        rev_move = self.env['account.move'].sudo().browse(res['res_id']) if 'res_id' in res else False
        if rev_move and rev_move.state == 'posted' and not rev_move.invn_sent:
            try:
                rev_move.create_and_export_invn()
            except:
                pass
        for move in moves:
            invoice_ref = move.invoice_origin or False
            sale = invoice_ref and sale_obj.search([('name', '=', invoice_ref)], limit=1) or False
            if sale:
                sale_dr_move_ids = move.reversal_move_id
                sale_dr_move_ids.x_edi_accounting_id = sale.x_edi_accounting_id
                sale_dr_move_ids.x_edi_store_number = sale.x_edi_store_number
                sale_dr_move_ids.x_studio_edi_reference = sale.client_order_ref
                sale_dr_move_ids.x_edi_ship_to_type = sale.partner_shipping_id.x_edi_ship_to_type
                sale_dr_move_ids.x_edi_transaction_type = 'CR'
                sale_dr_move_ids.sale_order_of = sale.order_of
        return res
