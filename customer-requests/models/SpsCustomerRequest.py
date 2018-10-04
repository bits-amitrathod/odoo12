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
    sale_order_id = fields.Char(String="Sale Order", compute="_get_sale_order_id")

    customer_sku = fields.Char()
    sps_sku = fields.Char()
    status = fields.Char()
    un_mapped_data = fields.Text()
    contact_id = fields.Integer()
    qty_to_show = fields.Char(compute="_get_qty_to_show")

    vendor_pricing = fields.Char()
    quantity = fields.Integer()
    required_quantity = fields.Integer()
    frequency_of_refill = fields.Integer()
    threshold = fields.Integer()
    uom = fields.Char()
    product_description = fields.Char(string='Product Description')
    customer_request_logs = fields.Char(string='Customer Request Logs')

    # Get Customer Requests
    def get_customer_requests(self):
        sps_customer_requests = self.env['sps.customer.requests'].search(
            [('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed', 'InCoolingPeriod', 'New'))])
        if len(sps_customer_requests)>0:
            try:
                self.process_customer_requests(sps_customer_requests)
            except Exception as exc:
                _logger.debug("Error procesing requests %r", exc)

    def process_customer_requests(self, sps_customer_requests):
        pr_models = []
        _logger.debug('len of customer request %r ', str(len(sps_customer_requests)))
        for sps_customer_request in sps_customer_requests:
            _logger.debug('customer request %r, %r', sps_customer_request['customer_id'].id, sps_customer_request['product_id'].id)
            if sps_customer_request['product_id'].id and not sps_customer_request['product_id'].id is False:
                _setting_object = self.get_settings_object(sps_customer_request['customer_id'].id, sps_customer_request['product_id'].id,
                                                            sps_customer_request['id'], sps_customer_request['status'])

                if _setting_object:
                    sps_customer_request.write({'customer_request_logs': 'Customer prioritization setting is True, '})
                    pr_model = dict(customer_request_id=sps_customer_request.id,
                                    template_type=sps_customer_request.document_id.template_type,
                                    customer_id=sps_customer_request['customer_id'].id,
                                    product_id=sps_customer_request['product_id'].id,
                                    status=sps_customer_request['status'],
                                    required_quantity=sps_customer_request.required_quantity,
                                    min_threshold=_setting_object.min_threshold,
                                    max_threshold=_setting_object.max_threshold,
                                    quantity=sps_customer_request.quantity,
                                    product_priority=_setting_object.priority,
                                    auto_allocate=_setting_object.auto_allocate,
                                    cooling_period=_setting_object.cooling_period,
                                    length_of_hold=_setting_object.length_of_hold,
                                    partial_order=_setting_object.partial_ordering,
                                    expiration_tolerance=_setting_object.expiration_tolerance,
                                    customer_request_logs = sps_customer_request.customer_request_logs)

                    pr_models.append(pr_model)

        #_logger.debug('Length **** %r', str(len(pr_models)))
        if len(pr_models) > 0:
            # Sort list by product priority
            pr_models = sorted(pr_models, key=itemgetter('product_priority'))
            # Allocate Product by priority.
            allocated_products = self.env['prioritization.engine.model'].allocate_product_by_priority(pr_models)

        return allocated_products

    def get_settings_object(self, customer_id,product_id,sps_customer_request_id,status):
        customer_level_setting = self.env['prioritization_engine.prioritization'].search(
            [('customer_id', '=', customer_id),('product_id', '=', product_id)])
        if len(customer_level_setting) == 1:
            if customer_level_setting.customer_id.prioritization:
                return customer_level_setting
            else:
                _logger.debug('Customer prioritization setting is False. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                if sps_customer_request_id != None and status != None:
                    self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False.")
                return False
        else:
            global_level_setting = self.env['res.partner'].search([('id', '=', customer_id)])
            if len(global_level_setting) == 1:
                if global_level_setting.prioritization:
                    return global_level_setting
                else:
                    _logger.debug('Customer prioritization setting is False. Customer id is :%r',
                                 str(global_level_setting.id))
                    if sps_customer_request_id != None and status != None:
                        self.update_customer_status(sps_customer_request_id, status, "Customer prioritization setting is False.")
                    return False

    def update_customer_status(self,sps_customer_request_id, status, log):
        if status.lower().strip() != 'unprocessed':
            # update status Unprocessed
            self.env['sps.customer.requests'].search(
                [('id', '=', sps_customer_request_id)]).write(dict(status="Unprocessed",customer_request_logs=log))

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
    def _get_sale_order_id(self):
        for record in self:
            if record.sale_order_line_id.id:
                if record.sale_order_id:
                    record.sale_order_id = str(record.sale_order_id)+ ", " +str(record.sale_order_line_id.order_id.id)
                else:
                    record.sale_order_id = str(record.sale_order_line_id.order_id.id)