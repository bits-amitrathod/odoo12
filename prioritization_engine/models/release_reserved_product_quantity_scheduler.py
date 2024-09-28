# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ReleaseReservedProductQuantityScheduler(models.Model):
    _name = 'release.reserved.product.quantity.cron.scheduler'
    _description = "Release Reserved ProductvQuantityvScheduler"

    @api.model
    #@api.multi
    def process_release_reserved_product_quantity_scheduler(self):
        _logger.info('In Release Reserved Product Quantity Scheduler')
        self.env['prioritization.engine.model'].release_reserved_product_quantity()