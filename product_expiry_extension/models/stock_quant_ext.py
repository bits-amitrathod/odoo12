from odoo import models, fields, api
import logging
import datetime


_logger = logging.getLogger(__name__)


class StockQuantExt(models.Model):
    _inherit = 'stock.quant'
    use_date = fields.Char('Expiration Date', compute='_compute_show_lot_user_date')

    def _compute_show_lot_user_date(self):
        for record in self:
            _logger.info(record.lot_id)
            if record.lot_id and record.lot_id.use_date:
                final_date = fields.Datetime.from_string(record.lot_id.use_date)
                record.use_date = final_date.date().strftime('%Y-%m-%d')
            else:
                record.use_date = ''