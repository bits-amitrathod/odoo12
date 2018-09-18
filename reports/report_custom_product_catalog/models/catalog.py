from odoo import api, fields, models

class ProductCatalogReport(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float("Product Qty", compute='_compare_qty', store=False)
    exp_min_date = fields.Date("Exp Min Date", store=False)
    exp_max_date = fields.Date("Exp Max Date", store=False)


    @api.multi
    def _compare_qty(self):
        for order in self:
            order.env.cr.execute("SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(order.id))
            query_result = order.env.cr.dictfetchone()
            if query_result['qut']:
                order.product_qty = query_result['qut']
            order.env.cr.execute( "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = " + str(order.id))
            query_result = order.env.cr.dictfetchone()
            if query_result['min'] :
                order.exp_min_date = fields.Datetime.from_string(str(query_result['min'])).date()
            if query_result['max'] :
                order.exp_max_date = fields.Datetime.from_string(str(query_result['max'])).date()