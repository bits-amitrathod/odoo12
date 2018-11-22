# -*- coding: utf-8 -*-

from odoo import models, fields, api
from operator import attrgetter
import logging
from operator import itemgetter


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

    customer_sku = fields.Char()
    mfr_catalog_no = fields.Char()
    sps_sku = fields.Char()
    status = fields.Char()
    un_mapped_data = fields.Text()
    contact_id = fields.Integer()
    qty_to_show = fields.Char(compute="_get_qty_to_show")

    vendor_pricing = fields.Char()
    quantity = fields.Float()
    required_quantity = fields.Float()
    frequency_of_refill = fields.Integer()
    threshold = fields.Integer()
    uom = fields.Char()
    product_description = fields.Char(string='Product Description')
    customer_request_logs = fields.Char(string='Customer Request Logs')

    document_id_set = set()

    # Get Customer Requests
    def get_customer_requests(self):
        _logger.info('In get_customer_requests')
        sps_customer_requests = self.env['sps.customer.requests'].search(
            [('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed', 'InCoolingPeriod', 'New', 'Partial'))])
        if len(sps_customer_requests)>0:
            try:
                self.process_customer_requests(sps_customer_requests)
            except Exception as exc:
                _logger.error("Error procesing requests %r", exc)


    def process_customer_requests(self, sps_customer_requests):
        _logger.info('In process_customer_requests')

        pr_models = []
        self.document_id_set.clear()
        _logger.debug('len of customer request %r ', str(len(sps_customer_requests)))
        for sps_customer_request in sps_customer_requests:
            # get latest customer uploaded document id
            self.env.cr.execute("SELECT max(id) document_id FROM public.sps_cust_uploaded_documents WHERE customer_id="+
                                str(sps_customer_request['customer_id'].id))
            query_result = self.env.cr.dictfetchone()

            # For Inventory Template
            if sps_customer_request.document_id.template_type.lower().strip() == 'inventory':
                # following condition use for process only latest uploaded document.
                if int(query_result['document_id']) == int(sps_customer_request.document_id.id):
                    pr_model = self.add_customer_request_data(sps_customer_request)
                    if pr_model:
                        pr_models.append(pr_model)
            # For Requirement Template, Process old document maximum 3 times and for new(latest) document processing no limit.
            elif sps_customer_request.document_id.template_type.lower().strip() == 'requirement':
                # following condition use for process only latest uploaded document.
                if int(query_result['document_id']) == int(sps_customer_request.document_id.id):
                    pr_model = self.add_customer_request_data(sps_customer_request)
                    if pr_model:
                        pr_models.append(pr_model)
                elif int(sps_customer_request.document_id.document_processed_count) < 3:
                    pr_model = self.add_customer_request_data(sps_customer_request)
                    if pr_model:
                        pr_models.append(pr_model)

        #_logger.debug('Length **** %r', str(len(pr_models)))
        if len(pr_models) > 0:
            # Sort list by product priority
            pr_models = sorted(pr_models, key=itemgetter('product_priority'))
            # Allocate Product by priority.
            self.env['prioritization.engine.model'].allocate_product_by_priority(pr_models)


    def add_customer_request_data(self,sps_customer_request):
        _logger.debug('customer request %r, %r', sps_customer_request['customer_id'].id,
                      sps_customer_request['product_id'].id)
        if sps_customer_request['product_id'].id and not sps_customer_request['product_id'].id is False:
            self.update_document_processed_count(sps_customer_request['document_id'].id,
                                                 sps_customer_request['document_id'].document_processed_count)
            _setting_object = self.get_settings_object(sps_customer_request['customer_id'].id,
                                                       sps_customer_request['product_id'].id,
                                                       sps_customer_request['id'], sps_customer_request['status'])

            # if status is partial check the remaining quantity to allocate to customer
            if sps_customer_request['status'].lower().strip() == 'partial':
                sale_order_line = self.env['sale.order.line'].search(
                    [('customer_request_id', '=', sps_customer_request.id)])
                _logger.debug('sale_order_line.product_uom_qty : %r', sale_order_line.product_uom_qty)
                required_quantity = sps_customer_request.required_quantity - sale_order_line.product_uom_qty
                _logger.debug('required_quantity : %r', required_quantity)
            else:
                required_quantity = sps_customer_request.required_quantity
            _logger.info('gl account value : %r',sps_customer_request['gl_account'])
            if _setting_object:
                sps_customer_request.write({'customer_request_logs': 'Customer prioritization setting is True, '})
                pr_model = dict(customer_request_id=sps_customer_request.id,
                                template_type=sps_customer_request.document_id.template_type,
                                customer_id=sps_customer_request['customer_id'].id,
                                gl_account=sps_customer_request['gl_account'],
                                product_id=sps_customer_request['product_id'].id,
                                status=sps_customer_request['status'],
                                required_quantity=required_quantity,
                                min_threshold=_setting_object.min_threshold,
                                max_threshold=_setting_object.max_threshold,
                                quantity=sps_customer_request.quantity,
                                product_priority=_setting_object.priority,
                                auto_allocate=_setting_object.auto_allocate,
                                cooling_period=_setting_object.cooling_period,
                                length_of_hold=_setting_object.length_of_hold,
                                partial_order=_setting_object.partial_ordering,
                                expiration_tolerance=_setting_object.expiration_tolerance,
                                customer_request_logs=sps_customer_request.customer_request_logs)
                return pr_model
        return False

    # check customer level or global level setting for product.
    def get_settings_object(self, customer_id,product_id,sps_customer_request_id,status):
        customer_level_setting = self.env['prioritization_engine.prioritization'].sudo().search(
            [('customer_id', '=', customer_id),('product_id', '=', product_id)])
        _logger.info("Inside get_settings_object"+str(customer_id)+" -"+str(product_id))
        _logger.info(len(customer_level_setting))
        if len(customer_level_setting) == 1:
            _logger.info("Inside get_settings_object if block")
            if customer_level_setting.customer_id.prioritization and customer_level_setting.customer_id.on_hold is False:
                if customer_level_setting.length_of_hold != 0:
                    return customer_level_setting
                else:
                    self.update_customer_status(sps_customer_request_id, status, "Product length of hold is 0. It should be minimum 1 hour")
                    return False
            else:
                _logger.info('Customer prioritization setting is False or customer is On Hold. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                if sps_customer_request_id != None and status != None:
                    self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False or customer is On Hold.")
                return False
        else:
            _logger.info("Inside get_settings_object else block")
            global_level_setting = self.env['res.partner'].sudo().search([('id', '=', customer_id)])
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
                    if sps_customer_request_id != None and status != None:
                        self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False or customer is On Hold.")
                    return False

    def update_customer_status(self,sps_customer_request_id, status, log):
        if status.lower().strip() != 'unprocessed':
            # update status Unprocessed
            self.env['sps.customer.requests'].search(
                [('id', '=', sps_customer_request_id)]).write(dict(status="Unprocessed",customer_request_logs=log))

    # update document processed count
    def update_document_processed_count(self, document_id, document_processed_count):
        if document_id not in self.document_id_set:
            self.document_id_set.add(document_id)
            _logger.info('document id : %r, document processed count : %r',document_id, document_processed_count)
            document_processed_count = int(document_processed_count) + 1
            self.env['sps.cust.uploaded.documents'].search([('id', '=', document_id)]).write(
                    dict(document_processed_count=document_processed_count))

    @api.multi
    @api.depends('document_id')
    def _get_qty_to_show(self):
        for record in self:
            if record.document_id.template_type == 'Requirement':
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
