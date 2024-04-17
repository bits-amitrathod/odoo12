from odoo import api, models, fields, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"
    _description = "Change Product Quantity"

    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number', required=True,
                             domain="[('product_id','=',product_id)]")
