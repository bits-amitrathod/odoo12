
from odoo import api, fields, models


class ProductVendorListView(models.Model):

    # _name='productvendorlist.productvendorlist'
    _inherit = 'purchase.order'
    # _auto=False

    last_sold = fields.Date('Last Sold',  store=False)
    cost=fields.Monetary(string='Cost', store=False)
    sku_code_product = fields.Char(string='SKU/Catelog No.', compute='_compute_product_vals', store=False)

    @api.onchange('cost')
    def _compute_product_vals(self):

        for order in self:
            product = self.env['product.product'].search([('id', '=', order.product_id.id)])
            order.sku_code_product=product.sku_code
            order.cost=product.list_price
            # order = "confirmation_date desc", limit = 1
            sale_orders = self.env['sale.order'].search([('product_id', '=', order.product_id.id), ('state', '=', 'sale')],order = "confirmation_date desc", limit = 1)
            for order_temp in sale_orders:
                order.last_sold=fields.Datetime.from_string(order_temp.confirmation_date).date()


            # order.env.cr.execute(
            #     "SELECT max(confirmation_date) FROM public.sale_order where product_id =" + str(order.product_id.id)) +" state ='sale'"
            # query_result = order.env.cr.dictfetchone()
            # if query_result['max'] != None:
            #     order.last_sold = fields.Datetime.from_string(str(query_result['max'])).date()

