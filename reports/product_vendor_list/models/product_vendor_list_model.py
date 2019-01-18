
from odoo import api, fields, models


class ProductVendorListView(models.Model):

    _inherit = 'purchase.order.line'
    # _auto=False

    last_sold = fields.Date('Last Sold', compute='_compute_product_vals',  store=False)
    cost=fields.Monetary(string='Cost', compute='_compute_product_vals', store=False)
    sku_code_product = fields.Char(string='Product SKU', compute='_compute_product_vals', store=False)
    partner_id=fields.Many2one(string="Vendor",compute='_compute_product_vals', store=False )

    @api.onchange('cost')
    def _compute_product_vals(self):

        for order in self:
            order.sku_code_product= order.product_id.sku_code
            order.last_sold = order.order_id.date_order
            order.cost = order.price_unit
            order.partner_id=order.order_id.partner_id.id


