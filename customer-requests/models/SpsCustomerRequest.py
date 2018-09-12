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
        _logger.info('In get_customer_requests()')
        sps_customer_requests = self.env['sps.customer.requests'].search(
            [('status', 'in', ('Inprocess', 'Incomplete', 'Unprocessed', 'InCoolingPeriod', 'New'))])
        if len(sps_customer_requests)>0:
            self.process_requests(sps_customer_requests)

    def process_requests(self, sps_customer_requests):
        pr_models = []
        _logger.debug('len of customer request %r ', str(len(sps_customer_requests)))
        for sps_customer_request in sps_customer_requests:
            _logger.debug('customer request %r, %r', sps_customer_request['customer_id'].id, sps_customer_request['product_id'].id)
            if sps_customer_request['product_id'].id and not sps_customer_request['product_id'].id is False:
                _setting_object = self._get_settings_object(sps_customer_request['customer_id'].id,
                                                        sps_customer_request['product_id'].id)
                if _setting_object:
                    pr_model = dict(customer_request_id=sps_customer_request.id,
                                    customer_id=sps_customer_request['customer_id'].id,
                                    product_id=sps_customer_request['product_id'].id,
                                    status=sps_customer_request['status'],
                                    required_quantity=sps_customer_request.required_quantity,
                                    product_priority=_setting_object.priority,
                                    auto_allocate=_setting_object.auto_allocate,
                                    cooling_period=_setting_object.cooling_period,
                                    length_of_hold=_setting_object.length_of_hold,
                                    partial_order=_setting_object.partial_ordering,
                                    expiration_tolerance=_setting_object.expiration_tolerance)

                    _logger.debug('customer request1 %r, %r, %r', pr_model['customer_request_id'], pr_model['customer_id'],
                                 pr_model['product_id'])
                    pr_models.append(pr_model)

        #_logger.debug('Length **** %r', str(len(pr_models)))
        if len(pr_models) > 0:
            # Sort list by product priority
            pr_models = sorted(pr_models, key=itemgetter('product_priority'))
            self.env['prioritization.engine.model'].allocate_product_by_priority(pr_models)


    def _get_settings_object(self, sps_customer_request):
        customer_level_setting = self.env['prioritization_engine.prioritization'].search(
            [('customer_id', '=', sps_customer_request['customer_id'].id),
             ('product_id', '=', sps_customer_request['product_id'].id)])
        if len(customer_level_setting) == 1:
            if customer_level_setting.customer_id.prioritization:
                return customer_level_setting
            else:
                _logger.debug('Customer prioritization setting is False. Customer id is :%r',
                             str(customer_level_setting.customer_id.id))
                self.update_customer_status(sps_customer_request)
                return False
        else:
            global_level_setting = self.env['res.partner'].search(
                [('id', '=', sps_customer_request['customer_id'].id)])
            if len(global_level_setting) == 1:
                if global_level_setting.prioritization:
                    return global_level_setting
                else:
                    _logger.debug('Customer prioritization setting is False. Customer id is :%r',
                                 str(global_level_setting.id))
                    self.update_customer_status(sps_customer_request)
                    return False

    def update_customer_status(self,sps_customer_request):
        if sps_customer_request['status'].lower().strip() != 'unprocessed':
            # update status Unprocessed
            self.env['sps.customer.requests'].search(
                [('id', '=', sps_customer_request['id'])]).write(dict(status="Unprocessed"))


