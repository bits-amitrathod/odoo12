# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
DOC_PREFIX_PO = '850'  # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860'  # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855'  # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
DOC_PREFIX_INV = '846'  # Prefix for Inventory Document

VARIABLE_855 = """ISA^00^{eleven_spaces}^00^{eleven_spaces}^ZZ^{supplier_id}^ZZ^{receiver_id}^{current_date_year_only}^{current_time}^U^00401^{interchange_number}^0^T^>~
GS^PR^{supplier_id_no_space}^{accounting_id}^{current_date}^{current_time}^8^X^004010~
ST^855^0001~
BAK^06^AC^{po_number}^{po_date_with_cc}^^^^{sale_order_name}^{sale_order_date_with_cc}~
REF^OQ^{ghx_order_ref}~
N1^ST^^91^{x_edi_store_number}~
N1^BT^^{fields_91_bt}^{x_billtoid}~
N1^SN^^{fields_92_sn}^{x_storeid}~
N1^VN^{seller_name}^{fields_92_vn}^{x_vendorid}~{so_lines}
CTT^{so_line_count}^14~
SE^{segment_count}^0001~
GE^1^8~
IEA^1^{interchange_number}~
"""
sale_line_str = """PO1^{line_num}^{quantity}^{uom}^{price_unit}^^VC^{vendor_part_number}^{in_qualifier}^{buyer_part_num}~
PID^F^^^^{vendor_part_description}~
ACK^{ack_code}^{product_uom_qty}^{uom}^017^{commitment_date_with_cc}^^VC^{vendor_part_number}~"""

POA_FIELDS = ['TRANSACTION ID', 'ACCOUNTING ID', 'PURPOSE', 'TYPE STATUS',
              'PO #', 'PO DATE', 'RELEASE NUMBER', 'REQUEST REFERENCE NUMBER',
              'CONTRACT NUMBER', 'SELLING PARTY NAME',
              'SELLING PARTY ADDRESS 1', 'SELLING PARTY ADDRESS 2',
              'SELLING PARTY CITY', 'SELLING PARTY STATE', 'SELLING PARTY ZIP',
              'ACCOUNT NUMBER - VENDOR NUMBER', 'WAREHOUSE ID', 'LINE #',
              'PO LINE #', 'VENDOR PART #', 'UPC', 'SKU', 'QTY', 'UOM',
              'PRICE', 'SCHEDULED DELIVERY DATE', 'SCHEDULED DELIVERY TIME',
              'ESTIMATED DELIVERY DATE', 'ESTIMATED DELIVERY TIME',
              'PROMISED DATE', 'PROMISED TIME', 'STATUS', 'STATUS QTY',
              'STATUS UOM']

ASN_FIELDS = ['TRANSACTION TYPE', 'ACCOUNTING ID', 'SHIPMENT ID', 'SCAC',
              'CARRIER PRO NUMBER', 'BILL OF LADING', 'SCHEDULED DELIVERY',
              'SHIP DATE', 'SHIP TO NAME', 'SHIP TO ADDRESS - LINE ONE',
              'SHIP TO ADDRESS - LINE TWO', 'SHIP TO CITY', 'SHIP TO STATE',
              'SHIP TO ZIP', 'SHIP TO COUNTRY', 'SHIP TO ADDRESS CODE',
              'SHIP VIA', 'SHIP TO TYPE', 'PACKAGING TYPE', 'GROSS WEIGHT',
              'GROSS WEIGHT UOM', 'NUMBER OF CARTONS SHIPPED',
              'CARRIER TRAILER NUMBER', 'TRAILER INITIAL', 'SHIP FROM NAME',
              'SHIP FROM ADDRESS - LINE ONE', 'SHIP FROM ADDRESS - LINE TWO',
              'SHIP FROM CITY', 'SHIP FROM STATE', 'SHIP FROM ZIP',
              'SHIP FROM COUNTRY', 'SHIP FROM ADDRESS CODE', 'VENDOR NUMBER',
              'DC CODE', 'TRANSPORTATION METHOD', 'PRODUCT GROUP', 'STATUS',
              'TIME SHIPPED', 'PO NUMBER', 'PO DATE', 'INVOICE NUMBER',
              'ORDER WEIGHT', 'STORE NAME', 'STORE NUMBER', 'MARK FOR CODE',
              'DEPARTMENT NUMBER', 'ORDER LADING QUANTITY', 'PACKAGING TYPE',
              'UCC-128', 'PACK SIZE', 'INNER PACK PER OUTER PACK',
              'PACK HEIGHT', 'PACK WIDTH', 'PACK WEIGHT',
              'QTY OF UPCS WITHIN PACK', 'UOM OF UPCS', 'STORE NAME',
              'STORE NUMBER', 'LINE NUMBER', 'VENDOR PART NUMBER',
              'BUYER PART NUMBER', 'UPC NUMBER', 'ITEM DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'QUANTITY ORDERED', 'UNIT PRICE',
              'PACK SIZE', 'PACK UOM', 'INNER PACKS PER OUTER PACK']
import time
import pytz
import csv
import pysftp
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    file_ref = fields.Char()
    x_edi_reference = fields.Char('EDI Reference', copy=False, store=False, compute='_compute_ref')
    x_edi_accounting_id = fields.Char('Accounting ID', copy=False, compute='_compute_sale_edi_values', store=False)
    x_edi_store_number = fields.Char('Store number', related='partner_shipping_id.x_edi_store_number', copy=False)
    x_edi_flag = fields.Boolean('EDI Flag', copy=False)
    poack_created = fields.Boolean(string="Acknowledged?", copy=False)
    customer_po_ref = fields.Many2one('setu.edi.log', copy=False)
    poack_ref = fields.Many2one('setu.edi.log', copy=False)
    order_of = fields.Selection([('true', 'Truecommerce'), ('ghx', 'GHX')])
    x_hdr_ref1 = fields.Char('Order Ref')
    x_hdr_ref2 = fields.Char('Total Amount')

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.order_line.set_po_line_number()
        return res

    @api.depends('client_order_ref')
    def _compute_ref(self):
        for sale in self:
            sale.x_edi_reference = sale.client_order_ref

    @api.depends('partner_id.x_edi_accounting_id', 'partner_shipping_id.x_edi_store_number')
    def _compute_sale_edi_values(self):
        for record in self:
            record.x_edi_accounting_id = record.partner_id and record.partner_id.x_edi_accounting_id or ''
            record.x_edi_store_number = record.partner_shipping_id and record.partner_shipping_id.x_edi_store_number or ''

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if not res.x_edi_accounting_id:
            res._compute_sale_edi_values()
        return res

    def create_poack_export_log_id(self):
        """
        Will create 855 type of log.

        @return: log_id: log_id of sale_id.
        """
        user_tz = pytz.timezone(self.env.user.tz or 'utc')
        po_date = str(self.date_order.astimezone(user_tz).date()) or (
                    self.customer_po_ref and self.customer_po_ref.po_date and str(self.customer_po_ref.po_date)) or ''
        log_id = self.env['setu.edi.log'].create({
            'po_number': self.client_order_ref,
            'type': 'export',
            'document_type': '855',
            'sale_id': self.id,
            'po_date': po_date,
            'x_hdr_ref1': self.customer_po_ref.x_hdr_ref1 if self.customer_po_ref else False
        })
        export_log = self.env['setu.poack.export.log.line']

        for line in self.order_line:
            export_log.create({
                'accounting_id': self.x_edi_accounting_id,
                'po_number': self.client_order_ref,
                'vendor_part': line.product_id.default_code,
                'po_date': po_date,
                'company_id': self.company_id.id,
                'x_edi_po_line_number': line.x_edi_po_line_number,
                'product_template_id': line.product_template_id.id,
                'qty': line.po_log_line_id and line.po_log_line_id.quantity or line.product_uom_qty,
                'uom': line.po_log_line_id and line.po_log_line_id.uom or line.product_uom.name,
                'price_unit': line.price_unit,
                'commitment_date': self.commitment_date and str(self.commitment_date.astimezone(user_tz).date()),
                'x_edi_status': line.x_edi_status,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.name,
                'edi_log_id': log_id.id,
                'line_num': line.x_edi_po_line_number,
                'upc_num': line.product_id.barcode or line.upc_num,
                'sale_line_id': line.id,
                'buyer_part_number': line.po_log_line_id and line.po_log_line_id.buyers_part_num or '',
                'x_hdr_ref1': line.po_log_line_id and line.po_log_line_id.edi_log_id and line.po_log_line_id.edi_log_id.x_hdr_ref1 or ''
            })
        return log_id

    def create_poack_export_log(self, sftp):
        """
        Will create POACK log.
        @param sftp: sftp instance.
        @return:
        """
        log_id = self.create_poack_export_log_id()
        self.poack_ref = log_id
        res = self.poack_export(sftp)
        if res:
            log_id.status = 'success'
        else:
            log_id.status = 'fail'
        return log_id

    def poack_export(self, sftp):
        """
        Will upload 855 .csv file on sftp server.
        @param sftp: sftp instance
        @return: True or False
        """
        DOC_PREFIX_POA = '855'
        log_id = self.poack_ref
        company = self.company_id
        sftp_conf = self.env['setu.sftp'].search([('company_id', '=', company.id),
                                                  ('instance_active', '=', True),
                                                 ('instance_of', '=', self.order_of)])
        ftpdpath = sftp_conf['ftp_poack_dpath']
        instance_of = 'TrueCommerce' if sftp_conf.instance_of == 'true' else 'GHX'
        now = datetime.now()
        current_date_year_only = now.date().strftime('%y%m%d')
        current_date = now.date().strftime('%Y%m%d')
        # current_date_with_cc = now.strftime('CCYYMMDD')
        current_time = now.strftime('%H%M')
        file_current_date = now.strftime("%Y%m%d%H%S")
        if instance_of == 'TrueCommerce':
            file_name = '/tmp/' + str(DOC_PREFIX_POA) + '_' + str(self.client_order_ref) + str(self.partner_id.name) + \
                        '_' + '.csv'  # TO DO COMPLETE FILE NAME WITH CUSTOMER NAME
        else:
            actual_file_name = '855' + '_' + '%s' % self.name + '_' + '%s' % file_current_date + '.txt'
            file_name = '/tmp/' + actual_file_name  # TO DO COMPLETE FILE NAME WITH CUSTOMER NAME
        with open(file_name, 'w+') as file_pointer:
            if instance_of == 'TrueCommerce':
                cvs_rows = []
                writer = csv.DictWriter(file_pointer, fieldnames=POA_FIELDS)
                writer.writeheader()
                for row in log_id.edi_855_log_lines:
                    cvs_rows.append({
                        'TRANSACTION ID': DOC_PREFIX_POA,
                        'ACCOUNTING ID': row.accounting_id,
                        'PURPOSE': 'null',  # ASK TIM FOR VALUE
                        'TYPE STATUS': 'null',
                        'PO #': row.po_number,
                        'PO DATE': row.po_date,
                        'RELEASE NUMBER': 'null',
                        'REQUEST REFERENCE NUMBER': row.po_number,
                        'CONTRACT NUMBER': 'null',
                        'SELLING PARTY NAME': company.name,
                        'SELLING PARTY ADDRESS 1': company.street and
                                                   company.street or 'null',
                        'SELLING PARTY ADDRESS 2': company.street2 and
                                                   company.street2 or 'null',
                        'SELLING PARTY CITY': company.city and
                                              company.city or 'null',
                        'SELLING PARTY STATE': company.state_id and
                                               company.state_id.name or 'null',
                        'SELLING PARTY ZIP': company.zip and
                                             company.zip or 'null',

                        'ACCOUNT NUMBER - VENDOR NUMBER': self.partner_id.edi_vendor_number or self.partner_shipping_id.edi_vendor_number,
                        'WAREHOUSE ID': 'null',
                        'LINE #': 'null',
                        'PO LINE #': row.line_num and
                                     row.line_num or 'null',
                        'VENDOR PART #': row.vendor_part or 'null',

                        'UPC': row.upc_num and
                               row.upc_num or 'null',
                        'SKU': 'null',
                        'QTY': row.qty and row.qty or 'null',
                        'UOM': row.uom and row.uom or 'null',
                        'PRICE': row.price_unit and row.price_unit or 0.0,
                        'SCHEDULED DELIVERY DATE': row.commitment_date,
                        'SCHEDULED DELIVERY TIME': 'null',
                        'ESTIMATED DELIVERY DATE': 'null',
                        'ESTIMATED DELIVERY TIME': 'null',
                        'PROMISED DATE': 'null',
                        'PROMISED TIME': 'null',
                        'STATUS': row.x_edi_status,
                        'STATUS QTY': row.product_uom_qty,
                        'STATUS UOM': row.product_uom
                    })
                writer.writerows(cvs_rows)
            elif instance_of == 'GHX':
                sale_order = log_id.sale_id
                date_order = sale_order.date_order or ''
                commitment_date = sale_order.commitment_date or ''
                commitment_date_with_cc = commitment_date and commitment_date.strftime('%Y%m%d')
                sale_order_date_with_cc = date_order and date_order.strftime('%Y%m%d')
                po_date = log_id.po_date
                customer = sale_order.partner_id
                sale_lines = ""
                first_line_po_date = False
                total_lines = len(log_id.edi_855_log_lines)
                for row in log_id.edi_855_log_lines:
                    sale_line = row.sale_line_id
                    product = sale_line.product_id
                    line = sale_line_str.format(line_num=row.line_num or '', quantity=int(row.qty), uom=row.uom or '',
                                                price_unit=sale_line.price_unit,
                                                vendor_part_number=product.default_code or '',
                                                buyer_part_num=row.buyer_part_number or '',
                                                vendor_part_description=product.name,
                                                in_qualifier='IN' if row.buyer_part_number else '',
                                                ack_code=sale_line.ack_code,
                                                product_uom_qty=int(sale_line.product_uom_qty),
                                                commitment_date_with_cc=commitment_date_with_cc
                                                )
                    if not first_line_po_date:
                        line = '\n' + line
                    sale_lines += line
                    if not po_date and row.po_date and not first_line_po_date:
                        po_date = row.po_date
                po_date = po_date and datetime.strptime(po_date, '%Y-%m-%d').strftime('%Y%m%d') or ''
                interchange_number = sftp_conf.update_interchange_number()
                file_content = VARIABLE_855.format(eleven_spaces=" " * 10,
                                                   supplier_id=sftp_conf.sender_id and sftp_conf.sender_id.ljust(
                                                       15) or " " * 15,
                                                   supplier_id_no_space=sftp_conf.sender_id or '',
                                                   receiver_id=sftp_conf.receiver_id and sftp_conf.receiver_id.ljust(
                                                       15) or " " * 15,
                                                   current_date_year_only=current_date_year_only,
                                                   current_time=current_time,
                                                   interchange_number=interchange_number or '',
                                                   accounting_id=sale_order.x_edi_accounting_id or '',
                                                   current_date=current_date,
                                                   po_number=sale_order.client_order_ref or '',
                                                   po_date_with_cc=po_date or '', sale_order_name=sale_order.name,
                                                   sale_order_date_with_cc=sale_order_date_with_cc,
                                                   ghx_order_ref=log_id.x_hdr_ref1 or (
                                                               self.customer_po_ref and self.customer_po_ref.x_hdr_ref1) or '',
                                                   x_edi_store_number=customer.x_edi_store_number or '',
                                                   x_billtoid=customer.x_billtoid or '',
                                                   x_storeid=customer.x_storeid or '',
                                                   x_vendorid=customer.x_vendorid or '',
                                                   so_line_count=total_lines,
                                                   included_segments=14,
                                                   so_lines=sale_lines,
                                                   seller_name=sftp_conf.company_name or 'Seller Name',
                                                   segment_count=7 + (total_lines * 3),
                                                   fields_91_bt='91' if customer.x_billtoid else '',
                                                   fields_92_sn='92' if customer.x_storeid else '',
                                                   fields_92_vn='92' if customer.x_vendorid else ''

                                                   )
                file_pointer.write(file_content)

            file_pointer.close()
            if sftp:
                sftp.cwd(ftpdpath)
                if instance_of == 'TrueCommerce':
                    sftp.put(file_name, ftpdpath + '/' + str(DOC_PREFIX_POA) + '_' + str(self.client_order_ref) + '_' + str(
                        self.name) + '.csv')
                else:
                    sftp.put(file_name, ftpdpath + '/' + actual_file_name)
                self.poack_created = True
                log_id.create_date = date.today()
                return True
            return False

    def get_edi_status(self):
        """
        This method will set edi status to order_lines.
        'accept' or 'reject'.
        @return:
        """
        lines = self.order_line
        for line in lines:
            if line.product_uom_qty > 0:
                line.x_edi_status = 'accept'
            else:
                line.x_edi_status = 'reject'

    def action_confirm(self):
        """
        Will create 855 POACK when sale order is confirmed.
        It will assign edi values to pickings that are created.
        @return:
        """
        for record in self:
            if record.x_edi_accounting_id and record.partner_shipping_id.edi_855:
                record.get_edi_status()
        pop_error = False
        for rec in self:
            if not rec.x_edi_accounting_id and rec.partner_id.x_edi_flag and rec.partner_shipping_id.edi_855:
                pop_error = True
                if len(self) == 1:
                    raise ValidationError(
                        _("Please make sure the Accounting ID is properly set on the Customer so the PO Acknowledgment can be sent to the Customer"))
        res = super(SaleOrder, self).action_confirm()
        if res and not pop_error:
            for record in self:
                if record.x_edi_accounting_id and record.partner_shipping_id.edi_855 and not record.poack_created:
                    # if record.order_of == 'true':
                    record.creat_poack_log_and_poack_export()
                    pickings = record.picking_ids
                    for pick in pickings:
                        pick.write(
                            {'x_edi_accounting_id': record.x_edi_accounting_id,
                             'sale_order_of': record.order_of,
                             # 'ship_from_warehouse': pick.location_id.get_warehouse().id,
                             'edi_vendor_number': pick.partner_id.parent_id.edi_vendor_number if pick.partner_id.parent_id else pick.partner_id.edi_vendor_number,
                             'x_edi_ship_to_type': self.partner_shipping_id.x_edi_ship_to_type}
                        )
        return res

    def creat_poack_log_and_poack_export(self):
        """
        Main method to create 855 log and export 855 .csv file on sftp server.
        @return: log_ids:
        """
        log_ids = self.env['setu.edi.log']
        sftp_conf = self.env['setu.sftp'].search(
            [('company_id', '=', self.company_id.id),
             ('instance_active', '=', True),
             ('instance_of', '=', self.order_of)])
        if sftp_conf:
            sftp, status = sftp_conf.test_connection()
            for sale in self:
                if sftp:
                    log_ids |= sale.create_poack_export_log(sftp)
                else:
                    log_id = self.env['setu.edi.log'].create({
                        'po_number': sale.client_order_ref,
                        'type': 'export',
                        'document_type': '855',
                        'status': 'fail',
                        'exception': status,
                        'sale_id': sale.id
                    })
                    sale.poack_ref = log_id
                    log_ids |= log_id
            if sftp:
                sftp.close()
            return log_ids


class SaleAdvPayinv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """
        This inherited method will set edi values to invoice when it is created.
        @return:
        """
        res = super(SaleAdvPayinv, self).create_invoices()
        sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
        sale_cr_invoices = sale.invoice_ids.filtered(lambda inv: not inv.reversed_entry_id)
        sale_cr_invoices.x_edi_accounting_id = sale.x_edi_accounting_id
        sale_cr_invoices.x_studio_edi_reference = sale.client_order_ref
        sale_cr_invoices.x_edi_store_number = sale.x_edi_store_number
        sale_cr_invoices.x_edi_ship_to_type = sale.partner_shipping_id.x_edi_ship_to_type
        sale_cr_invoices.x_edi_transaction_type = 'DR'
        sale_cr_invoices.sale_order_of = sale.order_of
        return res
