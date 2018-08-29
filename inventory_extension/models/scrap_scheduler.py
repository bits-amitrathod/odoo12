# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class ScrapScheduler(models.Model):
    _inherit = 'stock.scrap'
    _name = 'stock.scrap'

    @api.model
    @api.multi
    def process_scrap_scheduler(self):
        today_date = datetime.datetime.now()
        today_start = fields.Datetime.to_string(today_date)
        location_id = self.env['stock.location'].search([('complete_name', '=', 'Physical Locations/WH/Stock')]).id
        stock_production_lot_ids = self.env['stock.production.lot'].search([('removal_date', '<=', today_start)])
        for stock_product_lot in stock_production_lot_ids:
            stock_ids=self.env['stock.quant'].search([('lot_id','=',stock_product_lot.id),('location_id', '=', location_id),('quantity', '>', 0)])
            for stock in stock_ids:
                val = {'location_id': location_id, 'date_expected': today_start, 'scrap_qty': int(stock.quantity),
                    'state': 'draft', 'product_id': int(stock.product_id), 'scrap_location_id': 4, 'owner_id': False,
                    'product_uom_id': int(stock_product_lot.product_uom_id), 'package_id': False, 'picking_id': False, 'origin': False,
                    'lot_id': int(stock.lot_id)}
                self=self.create(val)
                self.action_validate()
                
    



