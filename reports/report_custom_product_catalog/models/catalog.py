from odoo import api, fields, models
import datetime
import odoo.addons.decimal_precision as dp
class InventoryValuationPopUp(models.TransientModel):
    _name = 'popup.product.catalog'

    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):
        res_model = 'product.product'

        # self.env['stock_production_lot'].search([('create_date', '>=', str(s_date)), ('create_date', '<=', str(e_date)),
        #                                     ('state', 'not in', ('cancel', 'void')), ]).ids
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form,tree",
            "res_model": res_model,
            "domain": []
        }
        tree_view_id = self.env.ref('report_custom_product_catalog.product_list_view').id
        form_view_id = self.env.ref('product.product_template_form_view').id
        action['name'] = "Product Catalog"
        action['views'] = [(tree_view_id, 'tree'),(form_view_id, 'form')]

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code.sku_code))

        return action

class InventoryCustomProductPopUp(models.TransientModel):
    _name = 'popup.custom.product.catalog'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):
        res_model = 'product.product'

        # self.env['stock_production_lot'].search([('create_date', '>=', str(s_date)), ('create_date', '<=', str(e_date)),
        #                                     ('state', 'not in', ('cancel', 'void')), ]).ids
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form,tree",
            "res_model": res_model,
            "domain": []
        }

        if self.start_date or self.end_date:
           sql_query=""" select distinct array_agg(product_id) from stock_production_lot where """
           if self.end_date and self.start_date:
               e_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
               e_date = e_date + datetime.timedelta(days=1)
               sql_query =sql_query +  """ use_date>=date(%s)  and  use_date<=date(%s)"""
               self._cr.execute(sql_query, (str(self.start_date), str(e_date),))
           elif self.start_date:
               sql_query=sql_query +""" use_date>=date(%s) """
               self._cr.execute(sql_query, (str(self.start_date),))
           elif self.end_date:
               e_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
               e_date = e_date + datetime.timedelta(days=1)
               sql_query = sql_query + """ use_date<=date(%s)"""
               self._cr.execute(sql_query, (str(e_date),))

           product_ids = self._cr.fetchall()
           product_list=list(product_ids[0])
           action["domain"].append(('id', 'in', product_list[0]))

        tree_view_id = self.env.ref('report_custom_product_catalog.custom_list_view').id
        form_view_id = self.env.ref('product.product_template_form_view').id
        action['name'] = "Custom Product Catalog"
        action['views'] = [(tree_view_id, 'tree'),(form_view_id, 'form')]

        if self.sku_code:
            action["domain"].append(('sku_code', 'ilike', self.sku_code.sku_code))

        return action

class ProductCatalogReport(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float("Product Qty", compute='_compare_qty', store=False,digits=dp.get_precision('Product Unit of Measure'))
    exp_min_date = fields.Date("Exp Min Date",compute='_compare_qty', store=False)
    exp_max_date = fields.Date("Exp Max Date",compute='_compare_qty', store=False)
    product_templ_id= fields.Many2one('product.template', 'Product Name', compute='_compare_qty', store=False)

    @api.multi
    def _compare_qty(self):
        for order in self:
            order.product_templ_id=order.product_tmpl_id.id
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
