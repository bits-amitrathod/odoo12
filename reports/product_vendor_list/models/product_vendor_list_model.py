
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
            order.cost=order.product_id.list_price

            sale_orders = self.env['sale.order'].search([('product_id', '=', order.product_id.id), ('state', '=', 'sale')],order = "confirmation_date desc", limit = 1)
            for order_temp in sale_orders:
                order.last_sold=fields.Datetime.from_string(order_temp.confirmation_date).date()

