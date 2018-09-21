# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PrioritizationScheduler(models.Model):
    _name = 'prioritization.cron.schedular'

    @api.model
    @api.multi
    def process_prioritization_scheduler(self):
        _logger.info('In PrioritizationScheduler')
        self.env['sps.customer.requests'].get_customer_requests()






