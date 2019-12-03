# -*- coding: utf-8 -*-

from odoo import models, fields, api
from operator import attrgetter
import logging
from operator import itemgetter


_logger = logging.getLogger(__name__)


class SpsCustomerRequest(models.Model):
    _name = 'sps.customer.requests'


    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    # cust_id=fields.Integer(related='customer_id.id')
    document_id = fields.Many2one('sps.cust.uploaded.documents', string='Document', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=False, default=0)
    sale_order_line_id = fields.One2many('sale.order.line', 'customer_request_id', string="Request")
    sale_order_name = fields.Char(string="Sale Order", compute="_get_sale_order_name")
    gl_account = fields.Char(string='GL Account')
    document_name = fields.Char(string="Document Name", compute="_get_document_name")

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
    customer_request_logs = fields.Char(string='Customer Request Logs')

    auto_allocate = fields.Boolean("Allow Auto Allocation")
    min_threshold = fields.Integer("Min Threshold")
    max_threshold = fields.Integer("Max Threshold")
    cooling_period = fields.Integer("Cooling Period in days")
    length_of_hold = fields.Integer("Length Of Hold in hours")
    expiration_tolerance = fields.Integer("Expiration Tolerance in months")
    partial_ordering = fields.Boolean("Allow Partial Ordering")
    partial_UOM = fields.Boolean("Allow Partial UOM")
    available_qty = fields.Integer("Available Quantity")
    document_id_set = set()
    documents = set()

    # Get Customer Requests
    def get_customer_requests(self):
        _logger.info('In get_customer_requests')

        get_all_in_process_doc = self.env['sps.cust.uploaded.documents'].search([('status', '=', 'In Process')])

        self.documents.clear()
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

        sps_customer_requests = self.env['sps.customer.requests'].search([('document_id.id', 'in', self.documents),
                                                                          ('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed','InCoolingPeriod', 'New', 'Partial'))],
                                                                         order="priority asc")

        self.process_customer_requests(sps_customer_requests)

    def process_customer_requests(self, sps_customer_requests):
        _logger.info('In process_customer_requests')
        self.env['prioritization.engine.model'].allocate_product_by_priority(sps_customer_requests)

    # check customer level or global level setting for product.
    def get_settings_object(self, customer_id,product_id,sps_customer_request_id,status):
        customer_level_setting = self.env['prioritization_engine.prioritization'].sudo().search(
            [('customer_id', '=', customer_id),('product_id', '=', product_id), ('priority', '>=', 0)])
        _logger.info("Inside get_settings_object"+str(customer_id)+" -"+str(product_id))
        _logger.info(len(customer_level_setting))
        if len(customer_level_setting) == 1:
            _logger.info("Inside get_settings_object if block")
            if customer_level_setting.customer_id.prioritization and customer_level_setting.customer_id.on_hold is False:
                if customer_level_setting.length_of_hold > 0:
                    return customer_level_setting
                elif sps_customer_request_id is not None and status is not None:
                    self.update_customer_status(sps_customer_request_id, status, "Product length of hold is 0. It should be minimum 1 hour")
                    return False
                else:
                    return False
            else:
                _logger.info('Customer prioritization setting is False or customer is On Hold. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                if sps_customer_request_id is not None and status is not None:
                    self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False or customer is On Hold.")
                return False
        else:
            _logger.info("Inside get_settings_object else block")
            global_level_setting = self.env['res.partner'].sudo().search([('id', '=', customer_id), ('priority', '>=', 0)])
            _logger.info(global_level_setting)
            if len(global_level_setting) == 1:
                if global_level_setting.prioritization and global_level_setting.on_hold is False:
                    if global_level_setting.length_of_hold != 0:
                        return global_level_setting
                    else:
                        self.update_customer_status(sps_customer_request_id, status, "Product length of hold is 0. It should be minimum 1 hour")
                        return False
                else:
                    _logger.info('Customer prioritization setting is False or customer is On Hold. Customer id is :%r',
                                 str(global_level_setting.id))
                    if sps_customer_request_id is not None and status is not None:
                        self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False or customer is On Hold.")
                    return False

    def update_customer_status(self,sps_customer_request_id, status, log):
        if status.lower().strip() != 'unprocessed':
            # update status Unprocessed
            self.env['sps.customer.requests'].search(
                [('id', '=', sps_customer_request_id)]).write({'status':'Unprocessed','customer_request_logs':log})

    @api.multi
    @api.depends('document_id')
    def _get_qty_to_show(self):
        for record in self:
            if record.document_id.template_type.lower().strip() == 'requirement':
                record.qty_to_show = str(record.required_quantity)
            else:
                record.qty_to_show = str(record.quantity)

    @api.multi
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

    @api.multi
    @api.depends('document_id')
    def _get_document_name(self):
        for record in self:
            record.document_name = str(record.document_id.document_name)