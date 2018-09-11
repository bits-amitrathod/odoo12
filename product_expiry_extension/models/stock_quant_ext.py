from odoo import models, fields, api
import logging
import datetime


_logger = logging.getLogger(__name__)



class StockQuantExt(models.Model):

    _inherit = 'stock.quant'
    use_date = fields.Char('Expiration Date', compute='_compute_show_lot_user_date')

    @api.multi
    def _compute_show_lot_user_date(self):
        for record in self:
            if record.lot_id and record.lot_id.use_date:
                final_date = fields.Datetime.from_string(record.lot_id.use_date)
                record.use_date = final_date.date()
