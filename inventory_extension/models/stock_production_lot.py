from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    use_date = fields.Datetime(string='Expiration Date',
                               help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')