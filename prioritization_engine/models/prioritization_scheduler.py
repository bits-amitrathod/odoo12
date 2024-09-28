# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class PrioritizationScheduler(models.Model):
    _name = 'prioritization.cron.schedular'
    _description = "Prioritization Scheduler"

    @api.model
    #@api.multi
    def process_prioritization_scheduler(self):
        _logger.info('In PrioritizationScheduler')
        try:
            self.env['sps.customer.requests'].get_customer_requests()
            self.env['prioritization.engine.model'].check_uploaded_document_status(None)
        except Exception as exc:
            _logger.error("Error processing requests %r", exc)

    def process_prioritization_scheduler_manually(self):
        _logger.info('In process_prioritization_scheduler_manually')
        try:
            self.env['sps.customer.requests'].get_customer_requests()
            self.env['prioritization.engine.model'].check_uploaded_document_status(None)
        except Exception as exc:
            _logger.error("Error processing requests %r", exc)

















