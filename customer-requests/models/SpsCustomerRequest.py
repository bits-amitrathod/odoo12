# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging


_logger = logging.getLogger(__name__)


class SpsCustomerRequest(models.Model):
    _name = 'sps.customer.requests'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    document_id = fields.Many2one('sps.cust.uploaded.documents', string='Document', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=False, default=0)
    sale_order_line_id = fields.One2many('sale.order.line', 'customer_request_id', string="Request")
    sale_order_name = fields.Char(string="Sale Order", compute="_get_sale_order_name")
    gl_account = fields.Char(string='GL Account')
    document_name = fields.Char(string="Document Name", compute="_get_document_name")
    manufacturer_oem_price = fields.Char(string="Price from OEM", compute="_get_manufacturer_oem_price")
    manufacturer_oem = fields.Char(string="Product OEM", compute="_get_product_oem")
    customer_product_description = fields.Char(string='Customer Product Description', compute="_get_customer_product_description")

    customer_sku = fields.Char()
    req_no = fields.Char()
    mfr_catalog_no = fields.Char()
    sps_sku = fields.Char()
    status = fields.Char()
    un_mapped_data = fields.Text()
    contact_id = fields.Integer()
    qty_to_show = fields.Char(compute="_get_qty_to_show")

    vendor_pricing = fields.Char()
    quantity = fields.Float()
    required_quantity = fields.Float()
    updated_quantity = fields.Float()
    frequency_of_refill = fields.Integer()
    threshold = fields.Integer()
    uom = fields.Char()
    priority = fields.Integer()
    uom_flag = fields.Boolean(help="if uom is each then set uom flag is 1(True)")
    product_description = fields.Char(string='Product Description')
    customer_request_logs = fields.Char(string='Customer Request Logs', default='')

    auto_allocate = fields.Boolean("Allow Auto Allocation")
    min_threshold = fields.Integer("Min Threshold")
    max_threshold = fields.Integer("Max Threshold")
    cooling_period = fields.Integer("Cooling Period in days")
    length_of_hold = fields.Integer("Length Of Hold in hours")
    expiration_tolerance = fields.Integer("Expiration Tolerance in months")
    partial_ordering = fields.Boolean("Allow Partial Ordering")
    partial_UOM = fields.Boolean("Allow Partial UOM")
    available_qty = fields.Integer("Available Quantity")
    duplicate_product = fields.Boolean('Duplicate Product')

    req_date = fields.Date(string='Requisition Date')
    vendor = fields.Char(string='Vendor')
    item_no = fields.Char(string='Item No.')
    deliver_to_location = fields.Char(string='Deliver-to Location')

    documents = set()

    # Get Customer Requests
    def get_customer_requests(self):
        _logger.info('In get_customer_requests')

        get_all_in_process_doc = self.env['sps.cust.uploaded.documents'].search([('status', '=', 'In Process')])

        self.documents.clear()
        if len(get_all_in_process_doc) > 0:
            for document in get_all_in_process_doc:
                doc_process_fixed_count = document.customer_id.doc_process_count
                document_processed_count = document.document_processed_count

                if document.template_type.lower().strip() == 'inventory':
                    self.env.cr.execute("SELECT max(id) document_id FROM public.sps_cust_uploaded_documents WHERE customer_id=" + str(document.customer_id.id))
                    query_result = self.env.cr.dictfetchone()
                    max_doc_id = int(query_result['document_id'])
                    # following condition use for process only latest uploaded document.
                    if int(max_doc_id) == int(document.id):
                        self.documents.add(document.id)
                        document.write({'document_processed_count': document.document_processed_count+1})
                    else:
                        if document.status != 'Completed':
                            document.write({'status': 'Completed'})
                elif document.template_type.lower().strip() == 'requirement':
                    if int(document_processed_count) < int(doc_process_fixed_count):
                        self.documents.add(document.id)
                        document.write({'document_processed_count': document.document_processed_count+1})

            sps_customer_requests = self.env['sps.customer.requests'].search([('document_id.id', 'in', list(self.documents)),
                                                                              ('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed','InCoolingPeriod', 'New', 'Partial')),
                                                                              '|', ('required_quantity', '>', 0), ('quantity', '>', 0)],
                                                                             order="priority asc")

            self.process_customer_requests(sps_customer_requests, tuple(self.documents))

    def process_customer_requests(self, sps_customer_requests, document_ids, source=None):
        _logger.info('In process_customer_requests')
        self.env['prioritization.engine.model'].allocate_product_by_priority(sps_customer_requests, document_ids, source)

    # check customer level or global level setting for product.
    def get_settings_object(self, customer_id, product_id):
        # get parent id
        parent_id = self.get_parent(customer_id)
        customer_level_setting = self.env['prioritization_engine.prioritization'].sudo().search(
            [('customer_id', '=', int(parent_id)), ('product_id', '=', int(product_id)), ('priority', '>=', 0)])
        _logger.info("Inside get_settings_object"+str(parent_id)+" -"+str(product_id))
        _logger.info(len(customer_level_setting))
        if len(customer_level_setting) == 1:
            _logger.info("Inside get_settings_object if block")
            if customer_level_setting.customer_id.prioritization and customer_level_setting.customer_id.on_hold is False:
                if customer_level_setting.length_of_hold > 0:
                    return customer_level_setting
                else:
                    return False
            else:
                _logger.info('Customer prioritization setting is False or customer is On Hold. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                return False
        else:
            _logger.info("Inside get_settings_object else block")
            global_level_setting = self.env['res.partner'].sudo().search([('id', '=', int(parent_id)), ('priority', '>=', 0)])
            _logger.info(global_level_setting)
            if len(global_level_setting) == 1:
                if global_level_setting.prioritization and global_level_setting.on_hold is False:
                    if global_level_setting.length_of_hold > 0:
                        return global_level_setting
                else:
                    _logger.info('Customer prioritization setting is False or customer is On Hold. Customer id is :%r',
                                 str(global_level_setting.id))
                    return False
            else:
                return False

    def get_parent(self, partner_id):
        partner = self.env['res.partner'].search([('id', '=', partner_id), ])
        parent_partner_id = None
        if partner:
            if partner.is_parent:
                parent_partner_id = partner.id
            elif partner.parent_id and partner.parent_id.id:
                parent_partner_id = partner.parent_id.id
            else:
                parent_partner_id = partner.id
        else:
            print('partner is inactive')
        return parent_partner_id

    @api.depends('document_id')
    def _get_qty_to_show(self):
        for record in self:
            if record.document_id.template_type.lower().strip() == 'requirement':
                record.qty_to_show = str(record.required_quantity)
            else:
                record.qty_to_show = str(record.quantity)

    @api.depends('sale_order_line_id')
    def _get_sale_order_name(self):
        sale_order_name_set = set()
        sale_order_name_set.clear()
        for record in self:
            sale_order_name_set.clear()
            for sale_order_line_id in record.sale_order_line_id:
                if sale_order_line_id.id:
                    sale_order_name_set.add(str(sale_order_line_id.order_id.name))
            if sale_order_name_set:
                record.sale_order_name = sale_order_name_set
            else:
                record.sale_order_name = None

    @api.depends('document_id')
    def _get_document_name(self):
        for record in self:
            record.document_name = str(record.document_id.document_name)

    def _get_product_oem(self):
        for record in self:
            if record.un_mapped_data:
                un_mapped_dict = record.un_mapped_data

                # removing spaces from keys, storing them in sam dictionary
                un_mapped_dict = {x.replace(' ', '').lower(): v for x, v in json.loads(un_mapped_dict).items()}

                if 'mfr.name' in un_mapped_dict:
                    record.manufacturer_oem = un_mapped_dict.get('mfr.name')
                elif 'manufacturer' in un_mapped_dict:
                    record.manufacturer_oem = un_mapped_dict.get('manufacturer')
                elif 'manufacturername' in un_mapped_dict:
                    record.manufacturer_oem = un_mapped_dict.get('manufacturername')
                elif 'productoem' in un_mapped_dict:
                    record.manufacturer_oem = un_mapped_dict.get('productoem')
                else:
                    record.manufacturer_oem = None

    def _get_manufacturer_oem_price(self):
        for record in self:
            if record.un_mapped_data:
                un_mapped_dict = record.un_mapped_data

                # removing spaces from keys, storing them in sam dictionary
                un_mapped_dict = {x.replace(' ', '').lower(): v for x, v in json.loads(un_mapped_dict).items()}

                if 'cost' in un_mapped_dict:
                    record.manufacturer_oem_price = un_mapped_dict.get('cost')
                elif 'price' in un_mapped_dict:
                    record.manufacturer_oem_price = un_mapped_dict.get('price')
                else:
                    record.manufacturer_oem_price = None

    def _get_customer_product_description(self):
        for record in self:
            if record.product_description and record.product_description is not None:
                record.customer_product_description = record.product_description
            elif record.un_mapped_data:
                un_mapped_dict = record.un_mapped_data

                # removing spaces from keys, storing them in sam dictionary
                un_mapped_dict = {x.replace(' ', '').lower(): v for x, v in json.loads(un_mapped_dict).items()}

                if 'description' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('description')
                elif 'productdescription' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('productdescription')
                elif 'desc' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('desc')
                elif 'desc.' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('desc.')
                elif 'product' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('product')
                elif 'productname' in un_mapped_dict:
                    record.customer_product_description = un_mapped_dict.get('productname')
                else:
                    record.customer_product_description = None
