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

    # def change_product_qty(self):
    #     """ Changes the Product Quantity by making a Physical Inventory. """
    #     Inventory = self.env['stock.inventory']
    #     for wizard in self:
    #         _logger.info("change lot numer extension : %r",wizard.lot_id.name)
    #         if wizard.lot_id.name is False:
    #             raise UserError(_('Lot Number is required.'))
    #
    #         product = wizard.product_id.with_context(location=wizard.location_id.id, lot_id=wizard.lot_id.id)
    #         line_data = wizard._action_start_line()
    #
    #
    #         if wizard.product_id.id and wizard.lot_id.id:
    #             inventory_filter = 'none'
    #         elif wizard.product_id.id:
    #             inventory_filter = 'product'
    #         else:
    #             inventory_filter = 'none'
    #         inventory = Inventory.create({
    #             'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
    #             'filter': inventory_filter,
    #             'product_id': wizard.product_id.id,
    #             'location_id': wizard.location_id.id,
    #             'lot_id': wizard.lot_id.id,
    #             'line_ids': [(0, 0, line_data)],
    #         })
    #         inventory.action_done()
    #     return {'type': 'ir.actions.act_window_close'}