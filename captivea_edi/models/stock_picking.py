# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import re
import pytz
import csv
from datetime import date, datetime
import pysftp
import logging

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

HEAD = """ISA^00^          ^00^          ^ZZ^{sender_id}^ZZ^{receiver_id}^{YYMMDD}^{HHMM}^U^00401^{interchange_number}^0^T^>~
GS^SH^{sender_id_with_no_space}^{accounting_id}^{current_date}^{current_time}^1^X^004010~
ST^856^0001~
BSN^00^{ship_id}^{date_done}^{date_done_time}~
HL^1^^S~{TD5_scac_line}
DTM^011^{date_done}~
N1^ST^^91^{store_num}~
N1^SF^{ship_from}^{fields_91_sf}^{vendor_number}~{n3_line}{n4_line}{vendor_reference}
HL^2^1^O~
PRF^{client_order_ref}~
REF^OQ^{order_ref}~{REF_CN_line}"""

LINE = """
HL^{seq}^2^I~
LIN^{line_num}^VC^{vendor_part}{in_buyer_part}~
SN1^{line_num}^{qty_done}^{uom}~"""

FOOT = """
CTT^{hl_count}~
SE^{lines_count}^0001~
GE^1^1~
IEA^1^{interchange_number}~"""

DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
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
              'PACK HEIGHT', 'PACK LENGTH', 'PACK WIDTH', 'PACK WEIGHT',
              'QTY OF UPCS WITHIN PACK', 'UOM OF UPCS', 'STORE NAME',
              'STORE NUMBER', 'LINE NUMBER', 'VENDOR PART NUMBER',
              'BUYER PART NUMBER', 'UPC NUMBER', 'ITEM DESCRIPTION',
              'QUANTITY SHIPPED', 'UOM', 'QUANTITY ORDERED', 'UNIT PRICE',
              'PACK SIZE', 'PACK UOM', 'INNER PACKS PER OUTER PACK']


class Picking(models.Model):
    _inherit = 'stock.picking'

    x_studio_edi_store_number = fields.Char('Store Number', copy=False)
    x_studio_scac = fields.Char(related='carrier_id.x_scac', copy=False)
    edi_log_ref = fields.Many2one('setu.edi.log', copy=False)
    x_edi_accounting_id = fields.Char('Accounting ID', copy=False)
    store_number = fields.Char('Store number', related='partner_id.x_edi_store_number', copy=False)
    x_studio_edi_packaging_type = fields.Selection([('Pallet', 'Pallet'), ('Carton', 'Carton')],
                                                   string='Packaging Type', default='Carton')
    x_edi_ship_to_type = fields.Selection([('DC', 'Warehouse Number'), ('SN', 'Store Number')], string='Ship To Type')
    edi_vendor_number = fields.Char('Customer Number')
    ship_to_name = fields.Char('Ship to name')
    ship_to_address_1 = fields.Char('Ship to address 1')
    ship_to_address_2 = fields.Char('Ship to address 2')
    ship_to_city = fields.Char('Ship to city')
    ship_to_state = fields.Char('Ship to state')
    ship_to_zip = fields.Char('Ship to zip')
    ship_to_country = fields.Char('Ship to country')
    ship_from_name = fields.Char('Ship from name')
    ship_from_warehouse = fields.Many2one('stock.warehouse', compute='get_ship_from_warehouse', store=False)
    ship_from = fields.Many2one('res.partner', compute='_compute_ship_from_address')
    ship_from_address_1 = fields.Char('Ship from address 1', compute='_compute_ship_from_address'
                                      )
    ship_from_address_2 = fields.Char('Ship from address 2', compute='_compute_ship_from_address'
                                      )
    ship_from_city = fields.Char('Ship from city', compute='_compute_ship_from_address')
    ship_from_state = fields.Char('Ship from state', compute='_compute_ship_from_address'
                                  )
    ship_from_zip = fields.Char('Ship from zip', compute='_compute_ship_from_address')
    ship_from_country = fields.Char('Ship from country', compute='_compute_ship_from_address'
                                    )
    x_studio_edi_carton_count = fields.Integer('Package Count', default=1, compute="_compute_package_count",
                                               store=False)
    asn_created = fields.Boolean('Notification Sent?')
    sale_order_of = fields.Selection([('true', 'Truecommerce'), ('ghx', 'GHX')], compute='_compute_sale_order_of',
                                     store=True)
    is_picking_of_edi = fields.Boolean(string='Is EDI and OUTGOING picking?', compute='_compute_is_picking_of_edi')

    def _compute_is_picking_of_edi(self):
        for pick in self:
            if pick.sale_id and pick.partner_id and pick.partner_id.edi_856 and pick.picking_type_id.code == 'outgoing':
                pick.is_picking_of_edi = True
            else:
                pick.is_picking_of_edi = False

    def _compute_ship_from_address(self):
        for rec in self:
            rec.ship_from = rec.ship_from_warehouse.partner_id
            rec.ship_from_address_1 = rec.ship_from.street
            rec.ship_from_address_2 = rec.ship_from.street2
            rec.ship_from_city = rec.ship_from.city
            rec.ship_from_state = rec.ship_from.state_id.name
            rec.ship_from_zip = rec.ship_from.zip
            rec.ship_from_country = rec.ship_from.country_id.name

    @api.depends('sale_id')
    def _compute_sale_order_of(self):
        for rec in self:
            if rec.sale_id:
                rec.sale_order_of = rec.sale_id.order_of
            else:
                rec.sale_order_of = False

    shipping_service = fields.Char(string="Shipping Service")
    x_scac_kuebix = fields.Char(string="X-SCAC")

    @api.depends('location_id')
    def get_ship_from_warehouse(self):
        for pick in self:
            pick.ship_from_warehouse = pick.location_id.warehouse_id

    def release_available_to_promise(self):
        res = super(Picking, self).release_available_to_promise()
        sale = self.env['sale.order'].search([('name', '=', self.sale_id.name)], limit=1)
        pickings = sale.picking_ids
        if pickings:
            pickings.filtered(lambda pick: pick.id != self.id).write({'x_edi_accounting_id': sale.x_edi_accounting_id,
                                                                      'x_studio_edi_store_number': sale.x_edi_store_number,
                                                                      'x_studio_edi_packaging_type': self.x_studio_edi_packaging_type
                                                                      })
            op_pick = pickings.filtered(lambda pick: pick.picking_type_id.code == 'outgoing')
            # pickings.write({
            #     'ship_from_warehouse': op_pick.location_id.get_warehouse().id
            # })
        return res

    @api.depends('package_ids', 'x_studio_edi_packaging_type')
    def _compute_package_count(self):
        for record in self:
            # record.x_studio_edi_carton_count = len(record.package_ids) if len(record.package_ids) > 1 else 1
            record.x_studio_edi_carton_count = len(record.move_line_ids_without_package) if len(
                record.move_line_ids_without_package) > 1 else 1

    @api.model
    def create(self, vals):
        picking = super(Picking, self).create(vals)

        picking.x_edi_accounting_id = picking.sale_id.x_edi_accounting_id or picking.backorder_id.x_edi_accounting_id
        picking.ship_to_name = picking.partner_id.name
        picking.ship_to_address_1 = picking.partner_id.street
        picking.ship_to_address_2 = picking.partner_id.street2
        picking.ship_to_city = picking.partner_id.city
        picking.ship_to_state = picking.partner_id.state_id.name
        picking.ship_to_country = picking.partner_id.country_id.name
        picking.ship_to_zip = picking.partner_id.zip
        picking.ship_from_name = picking.company_id.name
        return picking

    def create_asn(self, sftp):
        """
        Will upload 856 type of .csv file on sftp server.

        @param sftp: sftp instance.
        @return: True of False.
        """
        order = self.sale_id
        # BEGINS CREATE ASN
        sftp_conf = self.env['setu.sftp'].search(
            [('company_id', '=', self.company_id.id), ('instance_active', '=', True),
             ('instance_of', '=', self.sale_order_of)])
        if sftp_conf:
            ftpdpath = sftp_conf['ftp_shipack_dpath']
            file_name = '/tmp/' + str(DOC_PREFIX_ASN) + '_' + \
                        str(order.name) + 'OUT' + str(self.id) + '_' + str(order.partner_id.name) \
                        + '.csv' if self.sale_order_of == 'true' else '/tmp/' + str(
                DOC_PREFIX_ASN) + '_' + 'message_id' + str(datetime.now()) + '.txt'  # mayBe x_edi_reference is better
            with open(file_name, 'w') as file_pointer:
                if self.sale_order_of == 'true':
                    cvs_rows = []
                    writer = csv.DictWriter(file_pointer, fieldnames=ASN_FIELDS)
                    writer.writeheader()
                    line_count = 0

                    for row in self.edi_log_ref.edi_856_log_lines:
                        line_count += 1
                        cvs_rows.append({
                            'TRANSACTION TYPE': DOC_PREFIX_ASN,
                            'ACCOUNTING ID': row.accounting_id,
                            'SHIPMENT ID': row.shipment_id,
                            'SCAC': row.x_studio_scac,
                            'CARRIER PRO NUMBER': row.carrier_tracking_ref,
                            'BILL OF LADING': row.origin_sale_order.name,
                            'SCHEDULED DELIVERY': 'null',
                            'SHIP DATE': str(row.date_done) or False,
                            'SHIP TO NAME': row.ship_to_name,
                            'SHIP TO ADDRESS - LINE ONE':
                                row.ship_to_address_1 or 'null',
                            'SHIP TO ADDRESS - LINE TWO':
                                row.ship_to_address_2 or 'null',
                            'SHIP TO CITY': row.ship_to_city or 'null',
                            'SHIP TO STATE': row.ship_to_state or 'null',
                            'SHIP TO ZIP': row.ship_to_zip or 'null',
                            'SHIP TO COUNTRY': row.ship_to_country or 'null',
                            'SHIP TO ADDRESS CODE': 'null',
                            'SHIP VIA': row.ship_via or '',
                            'SHIP TO TYPE': row.x_edi_ship_to_type,
                            'PACKAGING TYPE': row.x_studio_edi_packaging_type,
                            'GROSS WEIGHT': row.weight,
                            'GROSS WEIGHT UOM': row.weight_uom_name,
                            'NUMBER OF CARTONS SHIPPED': row.x_studio_edi_carton_count,
                            'CARRIER TRAILER NUMBER': 'null',
                            'TRAILER INITIAL': 'null',

                            'SHIP FROM NAME': row.ship_from_company_id.name,
                            'SHIP FROM ADDRESS - LINE ONE': row.ship_from_street or 'null',
                            'SHIP FROM ADDRESS - LINE TWO': row.ship_from_street2 or 'null',
                            'SHIP FROM CITY': row.ship_from_city or 'null',
                            'SHIP FROM STATE': row.ship_from_state or 'null',
                            'SHIP FROM ZIP': row.ship_from_zip or 'null',
                            'SHIP FROM COUNTRY': row.ship_from_country or 'null',
                            'SHIP FROM ADDRESS CODE': 'null',
                            'VENDOR NUMBER': order.partner_id.edi_vendor_number,
                            'DC CODE': 'null',
                            'TRANSPORTATION METHOD': 'null',
                            'PRODUCT GROUP': 'null',
                            'STATUS': 'Complete Shipment ' if row.status == 'complete' else 'Partial Shipment',
                            'TIME SHIPPED': 'null',
                            'PO NUMBER': row.po_number,
                            'PO DATE': row.po_date,
                            'INVOICE NUMBER': 'null',
                            'ORDER WEIGHT': row.weight,
                            'STORE NAME': row.store_name,
                            'STORE NUMBER': row.store_number,
                            'MARK FOR CODE': 'null',
                            'DEPARTMENT NUMBER': 'null',
                            'ORDER LADING QUANTITY': row.x_studio_edi_carton_count or 'null',
                            'PACKAGING TYPE': row.x_studio_edi_packaging_type,
                            'UCC-128': row.ucc_128 or line_count,
                            'PACK SIZE': 'null',
                            'INNER PACK PER OUTER PACK': 'null',
                            'PACK HEIGHT': 'null',
                            'PACK LENGTH': 'null',
                            'PACK WIDTH': 'null',
                            'PACK WEIGHT': 'null',
                            'QTY OF UPCS WITHIN PACK': row.upc_within_pack,
                            'UOM OF UPCS': row.uom_of_upc,
                            'LINE NUMBER': line_count,
                            'VENDOR PART NUMBER': row.vendor_number or '',
                            'BUYER PART NUMBER': row.buyer_part_number,
                            'UPC NUMBER': row.upc,
                            'ITEM DESCRIPTION': row.description_sale,
                            'QUANTITY SHIPPED': row.quantity_done or 0.0,
                            'UOM': row.uom,
                            'QUANTITY ORDERED': row.product_uom_quantity or 0.0,
                            'UNIT PRICE': row.unit_price,
                            'PACK SIZE': 'null',
                            'PACK UOM': 'null',
                            'INNER PACKS PER OUTER PACK': 'null'
                        })
                    writer.writerows(cvs_rows)
                else:
                    current_date = str(date.today()).replace('-', '')
                    current_time = str(datetime.now().time()).replace(':', '')[0:4]
                    date_done = self.date_done and str(self.date_done.date()).replace('-', '')
                    date_done_time = self.date_done and str(self.date_done.time()).replace(':', '')[0:4]
                    seq = 2
                    x_interchange = sftp_conf.update_interchange_number()
                    REF_CN_line = ''

                    lines = """"""
                    # hl_count = 0
                    for line in self.move_ids_without_package:
                        seq += 1
                        quantity = line.quantity_done

                        line_uom = line.sale_line_id.product_uom
                        if line_uom and line_uom != line.product_uom:
                            quantity = line.product_uom._compute_quantity(quantity, line_uom)
                        buyers_part_num_str = line.sale_line_id.po_log_line_id.buyers_part_num or ''
                        lines += LINE.format(seq=seq or '',
                                             line_num=(line.sale_line_id.po_log_line_id and line.sale_line_id.po_log_line_id.line_num) or
                                                      (line.sale_line_id.x_edi_po_line_number) or '',
                                             buyer_part=line.sale_line_id.po_log_line_id and line.sale_line_id.po_log_line_id.buyers_part_num or '',
                                             in_qualifier='IN' if buyers_part_num_str else '',
                                             vendor_part=line.product_id.default_code or '',
                                             in_buyer_part = '^IN^%s'%(buyers_part_num_str) if buyers_part_num_str else '',
                                             qty_done=int(quantity) or '',
                                             uom=line.sale_line_id and line.sale_line_id.po_log_line_id and line.sale_line_id.po_log_line_id.uom or line.sale_line_id.product_uom.name or '')
                        # hl_count += 1
                    ship_name = self.name
                    ship_id = ship_name and '/' in ship_name and \
                              ship_name.rsplit("/", 1) and len(ship_name.rsplit("/", 1)) > 0 \
                              and ship_name.rsplit("/", 1)[1] or ''
                    domain = [('name', '=', self.ship_from_state)]
                    if self.ship_from_country:
                        domain.append(('country_id.name', '=', self.ship_from_country))
                    ship_from_state_id = self.ship_from_state and self.env['res.country.state'].sudo().search(domain, limit=1) or False
                    ship_from_state_code = ''
                    if ship_from_state_id:
                        ship_from_state_code = ship_from_state_id.code
                    TD5_scac_line = """
TD5^^2^%s~""" % (self.carrier_id and self.carrier_id.x_scac or '',)
                    if self.carrier_tracking_ref:
                        REF_CN_line = """
REF^CN^%s~""" % (self.carrier_tracking_ref or '')
                    customer_po_ref_id = order.customer_po_ref
                    vendor_id_str = customer_po_ref_id and customer_po_ref_id.vendor_id or ''
                    vendor_ref_str = customer_po_ref_id and customer_po_ref_id.vendor_ref or ''
                    vendor_reference = "\nN1^VN^{vendor_ref_str}^92^{vendor_id_str}~".format(
                        vendor_ref_str=vendor_ref_str,
                        vendor_id_str=vendor_id_str) if vendor_ref_str and vendor_id_str else ''
                    head = HEAD.format(
                        sender_id=sftp_conf.sender_id and sftp_conf.sender_id.ljust(15) or " " * 15,
                        receiver_id=sftp_conf.receiver_id and sftp_conf.receiver_id.ljust(15) or " " * 15,
                        sender_id_with_no_space=sftp_conf.sender_id or '',
                        YYMMDD=current_date[2:] or '',
                        HHMM=current_time or '',
                        interchange_number=x_interchange or '',
                        accounting_id=self.partner_id.parent_id and self.partner_id.parent_id.x_edi_accounting_id or '',
                        current_date=current_date or '',
                        current_time=current_time or '',
                        ship_id=ship_id,
                        TD5_scac_line=TD5_scac_line if self.carrier_id and self.carrier_id.x_scac else '',
                        date_done=date_done or '',
                        date_done_time=date_done_time or '',
                        
                        store_num=self.partner_id and self.partner_id.x_edi_store_number or '',
                        ship_from=self.ship_from and self.ship_from.name or '',
                        fields_91_sf='91' if self.ship_from and self.ship_from.edi_vendor_number else '',
                        vendor_number=self.ship_from and self.ship_from.edi_vendor_number or '',
                        add1=self.ship_from_address_1 or '',
                        add2=self.ship_from_address_2 or '',
                        city=self.ship_from_city or '',
                        state=self.ship_from_state or '',
                        client_order_ref=self.sale_id and self.sale_id.client_order_ref or '',
                        order_ref=self.sale_id and self.sale_id.x_hdr_ref1 or '',
                        REF_CN_line=REF_CN_line,
                        carrier_tracking_ref=self.carrier_tracking_ref or '',
                        # n2_line=f"\nN2^{self.ship_from_address_1}~" if self.ship_from_address_1 else '',
                        vendor_reference=vendor_reference,
                        n3_line=f"\nN3^{self.ship_from_address_1}~" if self.ship_from_address_1 else '',
                        n4_line=f"\nN4^{self.ship_from_city}^{ship_from_state_code}^{self.ship_from_zip}~" if self.ship_from_city or ship_from_state_code or self.ship_from_zip else '')
                    lines_count = (len(self.move_ids_without_package) * 3) + 13
                    if self.carrier_tracking_ref:
                        lines_count += 1
                    if self.carrier_id and self.carrier_id.x_scac:
                        lines_count += 1
                    foot = FOOT.format(interchange_number=x_interchange,
                                       lines_count=lines_count,
                                       hl_count=len(self.move_ids_without_package) + 2)
                    # + 2 <-- 2 HL count in HEAD section
                    res = head + lines + foot
                    file_pointer.write(res)

                file_pointer.close()
            if sftp:
                sftp.cwd(ftpdpath)
                try:
                    partner_name = order.partner_id.name
                    partner_name = re.sub('[^a-zA-Z0-9 \n\.]', '', partner_name)
                    if self.sale_order_of == 'true':
                        sftp.put(file_name,
                                 ftpdpath + '/' + str(DOC_PREFIX_ASN) + '_' + str(order.name) + '_' + str(
                                     self.name.replace('/', '_')) + '_' + \
                                 str(partner_name) + '.csv')
                    else:
                        date_time = str(datetime.now()).replace('-', '').replace(':', '')[0:13].replace(' ', '')
                        sftp.put(file_name,
                                 ftpdpath + '/' + str(DOC_PREFIX_ASN) + '_' + self.name.replace('/',
                                                                                            '_') + '_' + date_time + '.txt')
                except Exception as e:
                    _logger.info("==========%s=========="%e)
                return True
            return False
        return False

    def create_asg_log(self, moves, po_number):
        """
        It will create shipping notification log.

        @param moves: moves are move_ids_withot_package of picking.
        @param process: 'auto' created log or 'manual' created log.
        @param po_number: purchase order number from 850.
        @return: log_id:
        """
        log_id = self.env['setu.edi.log'].create({
            'po_number': po_number,
            'type': 'export',
            'document_type': '856'
        })
        for row in moves:
            if self.sale_order_of == 'true':
                log_line = self._create_856_log_line_by_package(row)
            else:
                log_line = self._create_856_log_line_ghx(row)
            log_id.write({
                'edi_856_log_lines': [(4, log_line.id)]
            })
        moves.picking_id.edi_log_ref = log_id
        if self.sale_order_of == 'ghx':
            log_id.x_hdr_ref1 = self.sale_id and self.sale_id.customer_po_ref and self.sale_id.customer_po_ref.x_hdr_ref1
        return log_id

    def _prepare_log_line_vals(self, row):
        user_tz = pytz.timezone(self.env.user.tz or 'utc')
        asn_log_vals = {
            'upc': row.product_id.barcode or row.move_id.sale_line_id.upc_num,
            'picking_id': row.picking_id.id,
            'accounting_id': row.picking_id.x_edi_accounting_id,
            'po_number': row.picking_id.sale_id.client_order_ref,
            'po_date': str(row.picking_id.sale_id.date_order.astimezone(
                user_tz).date()) if row.picking_id and row.picking_id.sale_id else False,
            'ship_from_company_id': row.picking_id.company_id.id,
            'ship_to_name': row.picking_id.partner_id.x_edi_store_number,
            'ship_to_address_1': row.picking_id.ship_to_address_1,
            'ship_to_address_2': row.picking_id.ship_to_address_2,
            'ship_to_city': row.picking_id.ship_to_city,
            'ship_to_state': row.picking_id.ship_to_state,
            'ship_to_zip': row.picking_id.ship_to_zip,
            'ship_to_country': row.picking_id.ship_to_country,
            'carrier_tracking_ref': row.picking_id.carrier_tracking_ref,
            'origin_sale_order': row.picking_id.sale_id.id,
            'date_done': str(row.picking_id.date_done.astimezone(user_tz).date()),
            'store_name': row.picking_id.partner_id.name,
            'shipment_id': row.picking_id.name,
            'x_studio_scac': row.picking_id.x_scac_kuebix,
            'carrier_id': False,
            'ship_via': self.shipping_service or False,
            'x_studio_edi_packaging_type': row.picking_id.x_studio_edi_packaging_type,
            'weight': row.picking_id.weight,
            'weight_uom_name': row.picking_id.weight_uom_name,
            'x_studio_edi_carton_count': row.picking_id.x_studio_edi_carton_count,
            'vendor_number': row.product_id.default_code,
            'uom': row.product_uom_id.name,

            'product_id': row.product_id.default_code,
            'description_sale': row.product_id.name,

            'ship_from_warehouse': row.picking_id.ship_from_warehouse.id,

            'unit_price': row.move_id.sale_line_id.price_unit,
            'buyer_part_number': row.move_id.sale_line_id.po_log_line_id.buyers_part_num,
            'x_edi_ship_to_type': row.picking_id.partner_id.x_edi_ship_to_type,

            'ucc_128': row.move_id.sale_line_id.x_edi_po_line_number
        }
        return asn_log_vals

    def _create_856_log_line_by_package(self, row):
        """
        Will create log lines for shipping notification type of log.

        @param row: row is line from move_ids_without_package of picking.
        @param process: 'auto' or 'manual' process. Used to calculate real product_uom_qty before picking was validated.
        @return: asn_log_vals: log_line_values
        """
        product_uom_qty = row.initial_product_uom_qty
        if row.initial_product_uom_qty == row.qty_done:
            status = 'complete'
        else:
            status = 'partial'

        package = row.result_package_id.quant_ids.filtered(lambda q: q.product_id == row.product_id)
        qty_upc_within_pack = package[0].quantity if package else False
        uom_of_upc = package[0].product_uom_id.name if package else False

        asn_vals = self._prepare_log_line_vals(row)
        asn_vals.update({
            'status': status,
            'product_uom_quantity': product_uom_qty,
            'quantity_done': row.qty_done,
            'upc_within_pack':
                qty_upc_within_pack or 'null',
            'uom_of_upc': uom_of_upc or 'null'
        })
        log_line = self.env['setu.shipack.export.log.line'].create(asn_vals)
        return log_line

    def _create_856_log_line_ghx(self, row):
        asn_vals = self._prepare_log_line_vals_ghx(row)
        asn_vals.update({
            'quantity_done': row.quantity_done,
            'product_uom_quantity': row.product_uom_qty
        })
        log_line = self.env['setu.shipack.export.log.line'].create(asn_vals)
        return log_line

    def _prepare_log_line_vals_ghx(self, row):
        user_tz = pytz.timezone(self.env.user.tz or 'utc')
        asn_log_vals = {

            'picking_id': row.picking_id.id,
            'accounting_id': row.picking_id.x_edi_accounting_id,
            'po_number': row.picking_id.sale_id.client_order_ref,
            'po_date': str(row.picking_id.sale_id.date_order.astimezone(
                user_tz).date()) if row.picking_id and row.picking_id.sale_id else False,
            'ship_from_company_id': row.picking_id.company_id.id,
            'ship_to_name': row.picking_id.partner_id.x_edi_store_number,
            'ship_to_address_1': row.picking_id.ship_to_address_1,
            'ship_to_address_2': row.picking_id.ship_to_address_2,
            'ship_to_city': row.picking_id.ship_to_city,
            'ship_to_state': row.picking_id.ship_to_state,
            'ship_to_zip': row.picking_id.ship_to_zip,
            'ship_to_country': row.picking_id.ship_to_country,
            'carrier_tracking_ref': row.picking_id.carrier_tracking_ref,
            'origin_sale_order': row.picking_id.sale_id.id,
            'date_done': str(row.picking_id.date_done.astimezone(user_tz).date()),
            'store_name': row.picking_id.partner_id.name,
            'shipment_id': row.picking_id.name,
            'x_studio_scac': row.picking_id.x_scac_kuebix,
            'carrier_id': False,
            'ship_via': self.shipping_service or False,
            # 'x_studio_edi_packaging_type': row.picking_id.x_studio_edi_packaging_type,
            # 'weight': row.picking_id.weight,
            # 'weight_uom_name': row.picking_id.weight_uom_name,
            # 'x_studio_edi_carton_count': row.picking_id.x_studio_edi_carton_count,
            'vendor_number': row.product_id.default_code,
            'uom': row.product_uom.name,

            'product_id': row.product_id.default_code,
            'description_sale': row.product_id.name,

            # 'ship_from_warehouse': row.picking_id.ship_from_warehouse.id,

            'unit_price': row.sale_line_id.price_unit,
            'buyer_part_number': row.sale_line_id.po_log_line_id.buyers_part_num,
            # 'x_edi_ship_to_type': row.picking_id.partner_id.x_edi_ship_to_type,

            # 'ucc_128': row.move_id.sale_line_id.x_edi_po_line_number
        }
        return asn_log_vals

    def _action_done(self):
        """
        This function is used to create ASNPn(856) file represent picking and
         its move line data. It will create .csv file into grab folder location
        :return:
        """
        for rec in self:
            if rec.sale_id:
                for move in rec.move_line_ids_without_package:
                    move.initial_product_uom_qty = move.reserved_qty
        res = super(Picking, self)._action_done()
        for record in self:
            # if self:
            if res and record.sale_id:
                if record.partner_id and record.partner_id.edi_856 and record.picking_type_id.code == 'outgoing' and not record.asn_created:
                    if record.sale_order_of == 'true':
                        record.create_asn_log_and_asn_export()
                    elif record.sale_order_of == 'ghx':
                        record.create_asn_log_and_asn_export_ghx()
        return res

    def create_asn_log_and_asn_export_ghx(self):
        log_ids = self.env['setu.edi.log']
        for pick in self:
            moves = pick.move_ids_without_package
            po_number = pick.sale_id.client_order_ref

            sftp_conf = pick.env['setu.sftp'].search(
                [('company_id', '=', pick.company_id.id), ('instance_of', '=', 'ghx'), ('instance_active', '=', True)])
            sftp, status = sftp_conf.test_connection()
            if sftp:
                log_id = pick.create_asg_log(moves, po_number)
                log_ids |= log_id
                ack = pick.create_asn(sftp)
                if ack:
                    log_id.status = 'success'
                    log_id.picking_ids = pick
                    pick.asn_created = True
                else:
                    log_id.status = 'fail'
            else:
                log_ids = self.env['setu.edi.log'].create({
                    'po_number': po_number,
                    'type': 'export',
                    'document_type': '856',
                    'status': 'fail',
                    'exception': status,
                    'picking_ids': pick.ids
                })
                pick.edi_log_ref = log_ids
        return log_ids

    def create_asn_log_and_asn_export(self):
        """
        Main method to create log and export both of 856 document.
        @param moves_value_dict: moves quantity values before picking is validated.
        @return: log_ids: will return log_ids of asn.
        """
        log_ids = self.env['setu.edi.log']
        for pick in self:
            moves = False
            picks = False
            bill_ship_picks_dict = self.env.context.get('bill_ship_picks_dict')

            if type(bill_ship_picks_dict) != dict:
                moves = pick.move_line_ids_without_package
                picks = pick
                process = 'auto'
            else:
                bill_ship = str(pick.sale_id.partner_id.id) + ',' + str(pick.partner_id.id)
                if bill_ship in bill_ship_picks_dict.keys():
                    common_address_picks = bill_ship_picks_dict[bill_ship]
                    moves = common_address_picks.move_line_ids_without_package
                    picks = bill_ship_picks_dict[bill_ship]
                    del bill_ship_picks_dict[bill_ship]
                process = 'manual'

            if moves:
                po_number = False
                # po_number_list = list(
                #     map(lambda sale: sale.x_edi_reference if sale.x_edi_reference else False, moves.picking_id.sale_id))
                po_number_list = moves.mapped('picking_id').mapped('sale_id').filtered(
                    lambda sale: sale.client_order_ref).mapped('client_order_ref')
                # po_number_list = [x for x in po_number_list if x]
                if po_number_list:
                    po_number = ", ".join(po_number_list)

                sftp_conf = self.env['setu.sftp'].search(
                    [('company_id', '=', pick.company_id.id), ('instance_of', '=', 'true'),
                     ('instance_active', '=', True)])
                sftp, status = sftp_conf.test_connection()
                if sftp:
                    log_id = pick.create_asg_log(moves, po_number)
                    log_ids |= log_id
                    ack = pick.create_asn(sftp)
                    if ack:
                        log_id.status = 'success'
                        if picks:
                            log_id.picking_ids = picks
                            picks.asn_created = True
                    else:
                        log_id.status = 'fail'
                else:
                    log_ids = self.env['setu.edi.log'].create({
                        'po_number': po_number,
                        'type': 'export',
                        'document_type': '856',
                        'status': 'fail',
                        'exception': status,
                        'picking_ids': picks.ids
                    })
                    picks.edi_log_ref = log_ids

        return log_ids


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    initial_product_uom_qty = fields.Float()
