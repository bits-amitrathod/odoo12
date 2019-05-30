from odoo import api, fields, models
import datetime
import odoo.addons.decimal_precision as dp


class InventoryValuationPopUp(models.TransientModel):
    _name = 'popup.product.catalog'

    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):

        tree_view_id = self.env.ref('report_custom_product_catalog.product_list_view').id
        form_view_id = self.env.ref('product.product_template_form_view').id

        action = {
            "name": "Product Catalog",
            "type": "ir.actions.act_window",
            "view_mode": "form,tree",
            "res_model": 'product.product',
            "views":  [(tree_view_id, 'tree'), (form_view_id, 'form')],
            "domain": []
        }

        if self.sku_code:
            action["domain"].append(('sku_code', '=', self.sku_code.sku_code))

        return action


class InventoryCustomProductPopUp(models.TransientModel):
    _name = 'popup.custom.product.catalog'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):

        tree_view_id = self.env.ref('report_custom_product_catalog.custom_list_view').id
        form_view_id = self.env.ref('product.product_template_form_view').id

        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form,tree",
            "res_model": 'product.product',
            "name": "Custom Product Catalog",
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': []
        }

        if self.start_date or self.end_date:
            product_ids = self.fetchData()

            product_list = list(product_ids[0])

            filtered_product_list = []

            for p_id in product_list[0]:
                flag = self.get_quantity(p_id)
                if flag:
                    filtered_product_list.append(p_id)

            action["domain"].append(('id', 'in', filtered_product_list))
            action["context"] = {'production_lot_ids': product_list[1]}

        if self.sku_code:
            action["domain"].append(('sku_code', '=', self.sku_code.sku_code))

        return action

    def fetchData(ctx):
        sql_query = """select array_agg(product_id), json_object_agg(product_id, id) from stock_production_lot 
        where """
        if ctx.end_date and ctx.start_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            sql_query = sql_query + """ use_date>=date(%s)  and  use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(ctx.start_date), str(e_date),))
        elif ctx.start_date:
            sql_query = sql_query + """ use_date>=date(%s) """
            ctx._cr.execute(sql_query, (str(ctx.start_date),))
        elif ctx.end_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            e_date = e_date + datetime.timedelta(days=1)
            sql_query = sql_query + """ use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(e_date),))

        return ctx._cr.fetchall()

    def get_quantity(self, product_id):
        self.env.cr.execute(
            "SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(
                product_id))
        query_result = self.env.cr.dictfetchone()

        if not query_result['qut'] is None and int(query_result['qut']) > 0:
            return True
        else:
            return False


class ProductCatalogReport(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float("Product Qty", compute='_compare_qty', store=False,
                               digits=dp.get_precision('Product Unit of Measure'))
    exp_min_date = fields.Date("Exp Min Date", compute='_compare_qty', store=False)
    exp_max_date = fields.Date("Exp Max Date", compute='_compare_qty', store=False)

    @api.multi
    def _compare_qty(self):
        for product in self:
            product.env.cr.execute(
                "SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(
                    product.id))
            query_result = product.env.cr.dictfetchone()

            if not query_result['qut'] is None and int(query_result['qut']) > 0:
                product.product_qty = query_result['qut']

                product.env.cr.execute(
                    "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = " + str(('production_lot_ids' in self._context and self._context['production_lot_ids'][str(product.id)]) or product.id))
                query_result = product.env.cr.dictfetchone()
                if query_result['min']:
                    product.exp_min_date = fields.Datetime.from_string(str(query_result['min'])).date()
                if query_result['max']:
                    product.exp_max_date = fields.Datetime.from_string(str(query_result['max'])).date()