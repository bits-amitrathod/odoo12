# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class PrioritizationScheduler(models.Model):
    _name = 'prioritization.cron.schedular'

    @api.model
    @api.multi
    def process_prioritization_scheduler(self):
        _logger.info('In PrioritizationScheduler')
        self.check_length_of_hold()
        self.env['sps.customer.requests'].get_customer_requests()

    def check_length_of_hold(self):
        _logger.info('In check_length_of_hold')

        sale_order_list = self.env['sale.order'].search([('state', 'in', ('sent','engine')), ('team_id.team_type', '=', 'engine')])

        for sale_order in sale_order_list:
            _logger.info('sale_order : %r', sale_order.id)
            sale_order_line_list = self.env['sale.order.line'].search([('order_id', '=', sale_order.id)])
            for sale_order_line in sale_order_line_list:
                _logger.info('sale_order_line : %r : %r',sale_order_line.id, sale_order_line.product_id.id)

            # length_of_hold = 0
            # sale_order['create_date'] + length_of_hold
            #
            # # get current datetime
            # current_datetime = datetime.now()















