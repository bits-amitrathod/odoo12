# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime

_logger = logging.getLogger(__name__)


class ScrapScheduler(models.TransientModel):
    _name = 'stock.scrap.scheduler'

    @api.model
    def process_scrap_scheduler(self, process_records=50):
        try:
            limit = process_records
            scrap_location = self.env['stock.location'].search([('name', '=', 'Scrapped'), ('active', '=', True)]).id
            today_start = fields.Date.to_string(datetime.datetime.now())
            # TODO: Using Query
            # query = """
            #     select sq.id from stock_quant sq
            #     inner join stock_lot sl
            #     on sl.id = sq.lot_id and sl.use_date < '{exp_date}' and sq.quantity > 0
            #     and sq.location_id in (select id from stock_location where usage='internal' and active=True)
            #     limit {limit_value}
            #  """.format(exp_date=today_start, limit_value=limit)
            # self.env.cr.execute(query)
            # stock_quant_ids = self.env.cr.dictfetchall()
            # id_list = [i['id'] for i in stock_quant_ids]
            # stock_quants = self.env['stock.quant'].search([('id', 'in', id_list)])
            domain = [
                        ('quantity', '>', 0),
                        ('location_id.usage', '=', 'internal'),
                        ('location_id.active', '=', True),
                        ('lot_id.use_date', '<', today_start),
                    ]
            stock_quants = self.env['stock.quant'].search(domain, limit=limit)
            _logger.info(f"Scrap scheduler {len(stock_quants)} lot(s) will be Processing")
            for stockq in stock_quants:
                scrap_data = {
                    'location_id': stockq.location_id.id,
                    'date_done': today_start,
                    'scrap_qty': int(stockq.quantity),
                    'state': 'draft',
                    'product_id': int(stockq.product_id),
                    'scrap_location_id': scrap_location,
                    'owner_id': False,
                    'product_uom_id': int(stockq.lot_id.product_uom_id.id),
                    'package_id': False,
                    'picking_id': False,
                    'origin': False,
                    'lot_id': int(stockq.lot_id.id)
                }
                ml = self.env['stock.scrap'].create(scrap_data)
                ml.action_validate()
        except Exception as e:
            _logger.error("Exception occurred while executing scrap scheduler....")
            _logger.error(e)

    def process_manual_scrap_scheduler(self):
        _logger.info("process_manual_scrap_scheduler called..")
        process_records = 50
        self.process_scrap_scheduler(int(process_records))
