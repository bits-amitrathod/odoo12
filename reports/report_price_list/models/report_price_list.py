from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api
import datetime
_logger = logging.getLogger(__name__)




class CustomerPriceList(models.Model):
    _name = "inv.customer_price_list"
    _description = "inventory customer price list"
    _rec_name = 'product_code'


    customer_name = fields.Char(string="Customer Name")
    cost = fields.Float(string="Cost")
    product_code = fields.Char(string="Product SKU")
    product_name = fields.Char(string="Product Name")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  readonly=True)
    currency_symbol=fields.Char(string="Currency Symbol")
    product_id = fields.Many2one('product.template', 'Product')



    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                    TRUNCATE TABLE "inv_customer_price_list"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)
        insert_query="""INSERT INTO inv_customer_price_list(customer_name, product_code, product_name, cost,currency_id,currency_symbol,product_id) values """
        customer_list=self.env.context.get('customer_list')
        product_ids = self.env.context.get('product_id')
        products = []
        price_list_id=[]
        product_price_list_item = self.env['product.pricelist.item'].search([('applied_on', '=', '3_global')])
        company_fetch = self.env['res.company'].search([], limit=1, order="id desc")
        if not customer_list is None and product_ids and not product_ids is None:
            for part in customer_list:
                for product in product_ids:
                    product_price = part.property_product_pricelist._get_product_price(product, 1.0)
                    values = "(%s,%s,%s,%s,%s,%s,%s)"
                    final_query = insert_query + " " + values
                    # self._cr.execute(final_query, (
                    # str(part.display_name), str(product.product_tmpl_id.sku_code), str(product.product_tmpl_id.name),
                    # str(product_price), str(product.product_tmpl_id.company_id.currency_id.id),
                    # str(product.product_tmpl_id.company_id.currency_id.symbol), str(product.product_tmpl_id.id)))
                    self._cr.execute(final_query, (
                        str(part.display_name), str(product.product_tmpl_id.sku_code),
                        str(product.product_tmpl_id.name),
                        str(product_price),
                        company_fetch.currency_id.id,
                        company_fetch.currency_id.symbol,
                        str(product.product_tmpl_id.id)))

        elif not customer_list is None :
            for part in customer_list:
                if product_price_list_item:
                    price_list_id = product_price_list_item.mapped('pricelist_id.id')
                if part.property_product_pricelist and part.property_product_pricelist.id in price_list_id:
                    products = self.env['product.product'].search([('active','=',True),('product_tmpl_id.type', '=', 'product')])
                elif part.property_product_pricelist:
                    product_price_list_item = self.env['product.pricelist.item'].search(
                        [('pricelist_id', '=', part.property_product_pricelist.id)])
                    product_ids = []
                    if product_price_list_item:
                        product = product_price_list_item.mapped('product_tmpl_id.id')
                        if product:
                            product=self.env['product.product'].search(
                                [('product_tmpl_id', 'in', product)]).ids
                            product_ids.extend(product)
                        product = product_price_list_item.mapped('product_id.id')
                        if product:
                            product_ids.extend(product)
                    products = self.env['product.product'].search(
                        [('id', 'in', product_ids)])
                _logger.info("res_partner : %r", part)
                for product in products:
                    product_price = part.property_product_pricelist._get_product_price(product, 1.0)
                    values="(%s,%s,%s,%s,%s,%s,%s)"
                    final_query=insert_query + " " + values
                    #self._cr.execute(final_query,(str(part.display_name),str(product.product_tmpl_id.sku_code),str(product.product_tmpl_id.name),str(product_price),str(product.product_tmpl_id.company_id.currency_id.id),str(product.product_tmpl_id.company_id.currency_id.symbol),str(product.product_tmpl_id.id)))
                    self._cr.execute(final_query, (
                    str(part.display_name), str(product.product_tmpl_id.sku_code), str(product.product_tmpl_id.name),
                    str(product_price),
                    company_fetch.currency_id.id,
                    company_fetch.currency_id.symbol,
                    str(product.product_tmpl_id.id)))

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

