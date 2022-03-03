# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
DOC_PREFIX_PO = '850'  # Prefix for Purchase Order Document
DOC_PREFIX_POC = '860'  # Prefix for Purchase Order Change Document
DOC_PREFIX_POA = '855'  # Prefix for Purchase Order Aknowledgment Document
DOC_PREFIX_ASN = '856'  # Prefix for Advanced Ship Notice Document
DOC_PREFIX_BIL = '810'  # Prefix for Invoice Document
DOC_PREFIX_INV = '846'  # Prefix for Inventory Document

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

import csv
import pysftp
from datetime import datetime, date, timedelta
from time import mktime
import time
import calendar
import pytz
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class CaptiveaEdiDocumentLog(models.Model):
    _name = 'captivea.edidocumentlog'
    _description = 'EDI processed log document'

    # active = fields.Boolean('Active?', default=True)
    edi_log_id = fields.Many2one('setu.edi.log', ondelete='cascade')
    log_type = fields.Selection([('success', 'Success'),
                                 ('fail', 'Failure')], default='fail')
    transaction_id = fields.Char('Transaction ID')
    accounting_id = fields.Char('Accounting ID')
    store_number = fields.Char('Store number')
    po_number = fields.Char('PO Number')
    po_date = fields.Char('PO Date')
    ship_to_name = fields.Char('Ship to name')
    ship_to_address_1 = fields.Char('Ship to address 1')
    ship_to_address_2 = fields.Char('Ship to address 2')
    ship_to_city = fields.Char('Ship to city')
    ship_to_state = fields.Char('Ship to state')
    ship_to_zip = fields.Char('Ship to zip')
    ship_to_country = fields.Char('Ship to country')
    bill_to_name = fields.Char('Bill to name')
    bill_to_address_1 = fields.Char('Bill to address 1')
    bill_to_address_2 = fields.Char('Bill to address 2')
    bill_to_city = fields.Char('Bill to city')
    bill_to_state = fields.Char('Bill to state')
    bill_to_zip = fields.Char('Bill to zip')
    bill_to_country = fields.Char('Bill to country')
    bill_to_code = fields.Char('Bill to code')
    ship_via = fields.Char('Ship via')
    ship_date = fields.Char('Ship date')
    terms = fields.Char('Terms')
    note = fields.Char('Note')
    department_number = fields.Char('Department number')
    cancel_date = fields.Char('Cancel date')
    do_not_ship_before = fields.Char('Do not ship before')
    do_not_ship_after = fields.Char('Do not ship after')
    allowance_percent_1 = fields.Char('Allowance percent 1')
    allowance_amount_1 = fields.Char('Allowance amount 1')
    allowance_percent_2 = fields.Char('Allowance percent 2')
    allowance_amount_2 = fields.Char('Allowance amount 2')
    line_num = fields.Char('Line #')
    vendor_part_num = fields.Char('Vendor part #')
    buyers_part_num = fields.Char('Buyers part #')
    upc_num = fields.Char('UPC #')
    description = fields.Char('Description')
    quantity = fields.Float('Quantity')
    uom = fields.Char('UOM')
    unit_price = fields.Float('Unit price')
    pack_size = fields.Float('Pack size')
    num_of_inner_packs = fields.Float('# of inner packs')
    item_allowance_percent = fields.Char('Item allowance percent')
    item_allowance_amount = fields.Char('Item allowance amount')
    state = fields.Char('Document State')
    line_state = fields.Char(default='fail')
    x_hdr_ref1 = fields.Char('Order Ref')
    x_hdr_ref2 = fields.Char()
    x_lin_ref1 = fields.Char('Line Ref 1')
    x_lin_ref2 = fields.Char('Line Ref 2')
    x_lin_ref3 = fields.Char('Line Ref 3')
    x_lin_ref4 = fields.Char('Line Ref 4')
    x_lin_ref5 = fields.Char('Line Ref 5')

    def _get_shipping_partner(self, new_record, partner):
        verify = False
        state = False
        country = False
        if new_record.state:
            if new_record.ship_to_country:
                country = self.env['res.country'].search([('code', '=ilike', new_record.ship_to_country[0:2])], limit=1)
                if country:
                    state = self.env['res.country.state'].search(
                        [('country_id', '=', country.id), ('code', '=ilike', new_record.ship_to_state[0:2])], limit=1)
                else:
                    verify = True
                    state = False
                    country = self.env['res.country'].create({
                        'name': new_record.ship_to_country,
                        'code': new_record.ship_to_country[0:2]
                    })
                if not state:
                    verify = True
                    state = self.env['res.country.state'].create({
                        'name': new_record.ship_to_state,
                        'country_id': country.id,
                        'code': new_record.ship_to_state[0:2]
                    })
            else:
                verify = True
                state = self.env['res.country.state'].search(
                    [('country_id.code', '=ilike', 'US'), ('code', '=ilike', new_record.ship_to_state[0:2])], limit=1)
                if state:
                    country = state.country_id
                else:
                    country = self.env['res.country'].search([('code', '=ilike', 'US')])
                    state = self.env['res.country.state'].create({
                        'name': new_record.ship_to_state,
                        'country_id': country.id,
                        'code': new_record.ship_to_state[0:2]
                    })

        shipping_partner = self.env['res.partner'].create({
            'type': 'delivery',
            'is_company': True,
            'parent_id': partner.id,
            'name': new_record.ship_to_name or partner.name + ' Delivery',
            'street': new_record.ship_to_address_1,
            'street2': new_record.ship_to_address_2,
            'city': new_record.ship_to_city,
            'state_id': state.id if state else False,
            'country_id': country.id if country else False,
            'zip': new_record.ship_to_zip,
            'x_edi_store_number': new_record.store_number,
            'x_edi_flag': True,
            'edi_810': True,
            'edi_855': True,
            'edi_856': True
        })
        return shipping_partner, verify

    def _get_ship_date(self, new_record, dt):
        """
        Will return ship_date and po_date from string got from 850 PO.

        @param new_record:
        @param dt: date type. ship date or po date.
        @return:
        """
        tz = self.env.user.tz or 'utc'
        zone = pytz.timezone(tz)
        zone_time = datetime.now(zone).time()
        if dt == 'ship':
            if new_record.ship_date:
                s_date = new_record.ship_date.split('/')
                ship_date = datetime(int(s_date[2]), int(s_date[0]), int(s_date[1]))
                ship_date = ship_date + timedelta(hours=zone_time.hour, minutes=zone_time.minute,
                                                  seconds=zone_time.second)
            else:
                today = datetime.now().replace(hour=zone_time.hour, minute=zone_time.minute, second=zone_time.second)

                if today.weekday() < 4:
                    ship_date = today + relativedelta(days=1)
                else:
                    ship_date = today + relativedelta(days=1)
            ship_date = zone.localize(ship_date)
            ship_date = ship_date.astimezone(pytz.utc)
            s_date = datetime(ship_date.year, ship_date.month, ship_date.day, ship_date.hour, ship_date.minute,
                              ship_date.second)
            return datetime.strptime(s_date.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
        elif dt == 'po':
            if new_record.po_date:
                if '/' in new_record.po_date:
                    s_date = new_record.po_date.split('/')
                    po_date = datetime(int(s_date[2]), int(s_date[0]), int(s_date[1])) + timedelta(hours=zone_time.hour,
                                                                                                   minutes=zone_time.minute,
                                                                                                   seconds=zone_time.second)
                else:
                    s_date= [new_record.po_date[0:4],new_record.po_date[4:6],new_record.po_date[6:8]]
                    po_date = datetime(int(s_date[0]), int(s_date[1]), int(s_date[2])) + timedelta(hours=zone_time.hour,
                                                                                                   minutes=zone_time.minute,
                                                                                                   seconds=zone_time.second)

            else:
                po_date = datetime.now().replace(hour=zone_time.hour, minute=zone_time.minute, second=zone_time.second)
            po_date = zone.localize(po_date)
            po_date = po_date.astimezone(pytz.utc)
            p_date = datetime(po_date.year, po_date.month, po_date.day, po_date.hour, po_date.minute,
                              po_date.second)
            return datetime.strptime(p_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

    def _check_price(self, line):
        """
        Will sent boolean if price is mismatching or not.
        @param line:
        @return:
        """
        price = line._get_display_price(line.product_id)
        if price == line.price_unit:
            return False
        return True

    def _create_sale_order_line(self, log_line, order, product):
        if not order.order_line.filtered(
                lambda line: line.x_edi_po_line_number == log_line.line_num and line.product_id.default_code == log_line.vendor_part_num):
            product_tmpl = self.env['product.template'].search([('name', '=', log_line.vendor_part_num)])
            new_order_line = {
                'edi_id': log_line.edi_log_id.id,
                'order_id': order.id,
                'product_id': product.id,
                'price_unit_850':log_line.unit_price,
                # 'price_unit': log_line.unit_price,
                'product_uom_qty': float(log_line.quantity),
                'x_edi_po_line_number': log_line.line_num,
                'product_template_id': product_tmpl.id,
                'upc_num': log_line.upc_num,
                'po_log_line_id': log_line.id
            }
            sale_order_line = self.env['sale.order.line']
            line = sale_order_line.sudo().create(new_order_line)
            price_mismatch = self._check_price(line)
            line.x_edi_mismatch = price_mismatch

    def _create_sale_order(self, log_id, file_ref):
        """
        Will create sale order from imported 850 Customer PO.
        @param log_id:
        @param file_ref: 850 file name on sftp server.
        @return:
        """
        order = self.env['sale.order'].search([('client_order_ref', '=', log_id.po_number),
                                               ('state', 'not in', ['sale', 'done']),
                                               ('file_ref', '=', file_ref)])
        so_vals = {}
        for log_line in log_id.edi_log_line_ids:
            product = self.env['product.product'].sudo().search(
                [('default_code', '=', log_line.vendor_part_num)],
                limit=1)
            if not order:
                partner = self.env['res.partner'].sudo().search(
                    [('x_edi_accounting_id', '=', log_line.accounting_id), ('parent_id','=', False)], limit=1)
                if partner and product:
                    shipping_partner = self.env['res.partner'].sudo().search(
                        [('x_edi_store_number', '=', log_line.store_number)], limit=1)
                    if shipping_partner == partner and log_line.store_number:
                        actual_shipping_partner = partner.child_ids.filtered(lambda sp: sp.type == 'delivery' and sp.x_edi_store_number == log_line.store_number)
                        if actual_shipping_partner:
                            shipping_partner = actual_shipping_partner
                    if not log_line.store_number:
                        shipping_partner = partner.child_ids.filtered(lambda sp: sp.type == 'delivery')
                    if not shipping_partner:
                        log_id.edi_log_line_ids.state = 'Pass! A new Delivery Address was created.'
                        shipping_partner, verify = self._get_shipping_partner(log_line, partner)
                        if verify:
                            log_id.edi_log_line_ids.state = 'Pass! Verify the delivery address created.'
                        else:
                            log_id.edi_log_line_ids.state = 'Pass! A new Delivery Address was created.'

                    else:
                        shipping_partner = shipping_partner[0]

                    ship_date = self._get_ship_date(log_line, 'ship')
                    po_date = self._get_ship_date(log_line, 'po')

                    so_vals.update({'partner_id': partner.id,
                                    'partner_shipping_id': shipping_partner.id,
                                    'date_order': po_date,
                                    'commitment_date': ship_date,
                                    'payment_term_id':partner.property_payment_term_id.id,
                                    # 'x_edi_reference': log_line.po_number,
                                    'x_edi_accounting_id': log_line.accounting_id,
                                    'client_order_ref': log_line.po_number,
                                    'x_edi_store_number': log_line.store_number,
                                    'customer_po_ref': log_id.id,
                                    'company_id': log_id.company_id.id,
                                    'file_ref': file_ref})

                    order = self.env['sale.order'].sudo().create(so_vals)
                    self._create_sale_order_line(log_line, order, product)
            else:
                self._create_sale_order_line(log_line, order, product)
        return order

    def create_and_add(self, vals, log_id):
        """
        Will create 850 import log lines.

        @param vals: line value dict.
        @param log_id: parent log id.
        @return:
        """
        new_record = self.create(vals)
        log_id.write({
            'edi_log_line_ids': [(4, new_record.id)]
        })
        return new_record
