from odoo import api, fields, models


class InventoryValuationPopUp(models.TransientModel):
    _name = 'popup.product.catalog'

    sku_code = fields.Char('Product SKU')

    def open_table(self):
        res_model = 'product.product'

        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form,tree",
            "res_model": res_model,
            "domain": []
        }

        is_custom_report = self.env.context.get('is_custom_report')
        if is_custom_report:
            tree_view_id = self.env.ref('report_custom_product_catalog.custom_list_view').id
            action['name'] = "Custom Product Catalog"
            action['views'] = [(tree_view_id, 'tree')]
        else:
            tree_view_id = self.env.ref('report_custom_product_catalog.product_list_view').id
            action['name'] = "Product Catalog"
            action['views'] = [(tree_view_id, 'tree')]

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code))

        return action


class ProductCatalogReport(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float("Product Qty", compute='_compare_qty', store=False)
    exp_min_date = fields.Date("Exp Min Date", store=False)
    exp_max_date = fields.Date("Exp Max Date", store=False)

    @api.multi
    def _compare_qty(self):
        for order in self:
            order.env.cr.execute(
                "SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(
                    order.id))
            query_result = order.env.cr.dictfetchone()
            if query_result['qut']:
                order.product_qty = query_result['qut']
            order.env.cr.execute(
                "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = " + str(
                    order.id))
            query_result = order.env.cr.dictfetchone()
            if query_result['min']:
                order.exp_min_date = fields.Datetime.from_string(str(query_result['min'])).date()
            if query_result['max']:
                order.exp_max_date = fields.Datetime.from_string(str(query_result['max'])).date()
