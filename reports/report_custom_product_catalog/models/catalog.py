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
            action["domain"].append(('name', '=', self.sku_code.name))

        return action


class InventoryCustomProductPopUp(models.TransientModel):
    _name = 'popup.custom.product.catalog'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    sku_code = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):

        tree_view_id = self.env.ref('report_custom_product_catalog.custom_list_view').id
        # form_view_id = self.env.ref('product.custom_form_view').id
        form_view_id = self.env.ref('report_custom_product_catalog.custom_form_view').id
        user_id =self._context.get('uid')
        print("----------------  user id  ---------------")
        print(user_id)

        sql_query = " DELETE FROM  cust_pro_catalog WHERE user_id = '"+str(user_id)+"'; "

        self._cr.execute(sql_query)

        insert = "INSERT INTO cust_pro_catalog (product_tmpl_id,sku,manufacture,name,qty,list_price,min_date,max_date,user_id )"
        part1 = insert + " SELECT  product_tmpl_id , sku, Manufacture, name, actual_quantity, list_price, min, max, user_id FROM (SELECT   min(l.use_date), max(l.use_date), sum(s.quantity), l.product_id FROM public.stock_lot as l  inner join  stock_quant  as s  on l.id = s.lot_id where " + (
            " l.product_id = " + str(self.sku_code.id) if self.sku_code  else " 1=1 ") + (
                    " and l.use_date > to_date('" + str(self.start_date) + "','YYYY-MM-DD')" if self.start_date else " and 1=1 ") + (
                    " and l.use_date < to_date('" + str(
                        self.end_date ) + "','YYYY-MM-DD')" if self.end_date else " and 1=1 ") + " and s.company_id != 0.0 group by l.product_id ) a left join (SELECT p.product_tmpl_id,p.id, pt.name,pt.actual_quantity ,pt.list_price, sku_code as sku, b.name as manufacture , '"+str(user_id)+"' as user_id FROM product_product p Inner join product_template pt ON  p.product_tmpl_id = pt.id INNER join product_brand b ON b.id = pt.product_brand_id) b ON a.product_id = b.id"
        # print(part1)
        self._cr.execute(part1)

        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": 'cust.pro.catalog',
            "name": "Custom Product Catalog",
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('user_id', '=', user_id)]
        }

        return action



class ProductCatalogReport(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float("Product Qty", compute='_compare_qty', store=False,
                               digits=dp.get_precision('Product Unit of Measure'))
    exp_min_date = fields.Date("Exp Min Date", store=False)
    exp_max_date = fields.Date("Exp Max Date", store=False)

    #@api.multi
    def _compare_qty(self):
        for product in self:
            product.env.cr.execute(
                "SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(
                    product.id))
            query_result = product.env.cr.dictfetchone()

            if not query_result['qut'] is None and int(query_result['qut']) > 0:
                product.product_qty = query_result['qut']

                product.env.cr.execute(
                    "SELECT min(use_date), max (use_date) FROM public.stock_lot where product_id = " + str(('production_lot_ids' in self._context and self._context['production_lot_ids'][str(product.id)]) or product.id))
                query_result = product.env.cr.dictfetchone()
                if query_result['min']:
                    product.exp_min_date = fields.Datetime.from_string(str(query_result['min'])).date()
                if query_result['max']:
                    product.exp_max_date = fields.Datetime.from_string(str(query_result['max'])).date()

class customeproductcata(models.Model):
    _name = 'cust.pro.catalog'
    _rec_name = 'product_tmpl_id'


    name = fields.Char(string=" Product Name")
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    min_date = fields.Date(string="Min Exp Date")
    max_date = fields.Date(string="Max Exp Date")
    currency_id = fields.Many2one(related='product_tmpl_id.currency_id', string="Currency", readonly=True,
                                  required=True)
    qty = fields.Integer("Product Qty")
    list_price = fields.Monetary("Price", currency_field='currency_id')
    sku = fields.Char(string="Product SKU")
    manufacture = fields.Char(string="Manufacture")
    user_id = fields.Char("User Id")

    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                    TRUNCATE TABLE "cust_pro_catalog"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()
