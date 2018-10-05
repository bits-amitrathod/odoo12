# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
import calendar
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class ScrapScheduler(models.Model):
    _name = 'stock.scrap.scheduler'

    @api.model
    @api.multi
    def process_scrap_scheduler(self):
        today_date = datetime.datetime.now()
        today_start = fields.Date.to_string(today_date)
        today_day=int(today_date.day)
        today_month=int(today_date.month)
        today_year=int(today_date.year)
        location_ids = self.env['stock.location'].search([('usage', '=', 'internal'),('active', '=', True)])
        stock_production_lot_ids = self.env['stock.production.lot'].search([('use_date', '<=', today_start)])
        last_day = int(calendar.monthrange(today_date.year, today_date.month)[1])
        for stock_product_lot in stock_production_lot_ids:
            lot_date=datetime.datetime.strptime(stock_product_lot.use_date, '%Y-%m-%d %H:%M:%S')
            use_day=int(lot_date.day)
            use_month=int(lot_date.month)
            use_year = int(lot_date.year)
            if use_day == 1 and today_day != last_day and today_month == use_month and today_year == use_year :
                continue
            for location_id in location_ids:
                stock_ids=self.env['stock.quant'].search([('lot_id','=',stock_product_lot.id),('location_id', '=', location_id.id),('quantity', '>', 0)])
                for stock in stock_ids:
                    scrap_id=self.env['stock.location'].search([('name', '=', 'Scrapped'), ('active', '=', True)]).id
                    val = {'location_id': location_id.id, 'date_expected': today_start, 'scrap_qty': int(stock.quantity),
                        'state': 'draft', 'product_id': int(stock.product_id), 'scrap_location_id': scrap_id, 'owner_id': False,
                        'product_uom_id': int(stock_product_lot.product_uom_id), 'package_id': False, 'picking_id': False, 'origin': False,
                        'lot_id': int(stock.lot_id)}
                    self=self.create(val)
                    self.action_validate()

    
    def process_manual_scrap_scheduler(self):
        _logger.info("process_manual_scrap_scheduler called..")
        self.process_scrap_scheduler()



