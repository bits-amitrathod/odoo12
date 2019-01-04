
from odoo import api, fields, models


class ProductVendorListView(models.Model):

    _inherit = 'purchase.order'
    # _auto=False

    last_sold = fields.Date('Last Sold',  store=False)
    cost=fields.Monetary(string='Cost', store=False)
    sku_code_product = fields.Char(string='Product SKU', compute='_compute_product_vals', store=False)

    @api.onchange('cost')
    def _compute_product_vals(self):

        for order in self:
            order.sku_code_product= order.product_id.sku_code
            order.last_sold = order.date_order

            for order_line in order.order_line:
                if order_line.product_id.id == order.product_id.id :
                    order.cost = order_line.price_unit
                    break

