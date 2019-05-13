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
        #self.env['fetchmail.server'].fetch_mail()
        self.env['sps.customer.requests'].get_customer_requests()

    def process_prioritization_scheduler_manually(self):
        _logger.info('In process_prioritization_scheduler_manually')
        #self.env['fetchmail.server'].search([('state', '=', 'done'), ('type', 'in', ['pop', 'imap'])]).fetch_mail()
        self.env['sps.customer.requests'].get_customer_requests()

















