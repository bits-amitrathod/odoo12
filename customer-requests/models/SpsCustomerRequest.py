# -*- coding: utf-8 -*-

from odoo import models, fields, api
from operator import attrgetter
import logging

_logger = logging.getLogger(__name__)


class SpsCustomerRequest(models.Model):

    _name = 'sps.customer.requests'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    document_id = fields.Many2one('sps.cust.uploaded.documents', string='Document', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=False, default=0)

    customer_sku = fields.Char()
    sps_sku = fields.Char()
    status = fields.Char()
    un_mapped_data = fields.Text()
    contact_id = fields.Integer()

    vendor_pricing = fields.Char()
    quantity = fields.Integer()
    required_quantity = fields.Integer()
    frequency_of_refill = fields.Integer()
    threshold = fields.Integer()
    uom = fields.Char()

    # Get Customer Requests
    def get_customer_requests(self):
        sps_customer_requests = self.env['sps.customer.requests'].search(
            [('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed', 'InCoolingPeriod', 'New'))])
        self.process_requests(sps_customer_requests)

    def process_requests(self, sps_customer_requests):
        pr_models = []
        _logger.info('len of customer request %r ', str(len(sps_customer_requests)))
        for sps_customer_request in sps_customer_requests:
            _logger.info('customer request %r, %r', sps_customer_request['customer_id'].id, sps_customer_request['product_id'].id)
            _setting_object = self._get_settings_object(sps_customer_request['customer_id'].id,
                                                        sps_customer_request['product_id'].id)
            if _setting_object:
                pr_model = self.pool.get('prioritization.engine.model')
                pr_model.customer_request_id = sps_customer_request.id
                pr_model.customer_id = sps_customer_request['customer_id'].id
                pr_model.product_id = sps_customer_request['product_id'].id
                pr_model.required_quantity = sps_customer_request.required_quantity
                pr_model.product_priority = _setting_object.priority
                pr_model.auto_allocate = _setting_object.auto_allocate
                pr_model.cooling_period = _setting_object.cooling_period
                pr_model.length_of_hold = _setting_object.length_of_hold
                pr_model.partial_order = _setting_object.partial_ordering
                pr_model.expiration_tolerance = _setting_object.expiration_tolerance
                _logger.info('customer request1 %r, %r, %r', pr_model.customer_request_id,pr_model.customer_id,
                             pr_model.product_id)

                pr_models.append(pr_model)
        self.env['prioritization.engine.model'].allocate_product_by_priority(pr_models)


    def _get_settings_object(self, customer_id, product_id):
        customer_level_setting = self.env['prioritization_engine.prioritization'].search(
            [('customer_id', '=', customer_id),
             ('product_id', '=', product_id)])
        if len(customer_level_setting) == 1:
            if customer_level_setting.customer_id.prioritization:
                return customer_level_setting
            else:
                _logger.info('Customer prioritization setting is False. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                return False
        else:
            global_level_setting = self.env['res.partner'].search(
                [('id', '=', customer_id)])
            if len(global_level_setting) == 1:
                if global_level_setting.prioritization:
                    return global_level_setting
                else:
                    _logger.info('Customer prioritization setting is False. Customer id is :%r',
                                 str(global_level_setting.id))
                    return False
