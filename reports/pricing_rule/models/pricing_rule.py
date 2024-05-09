from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api
import datetime
_logger = logging.getLogger(__name__)




class PricingRule(models.Model):
    _name = "res.pricing_rule"
    _description = "inventory pricing rule for customer"
    # _auto = False
    customer_name = fields.Char(string="Customer Name")
    product_id = fields.Many2one('product.template', string='Product', )
    partner_id = fields.Many2one('res.partner', string='Customer', )
    cost = fields.Float(string="Cost")
    product_code = fields.Char(string="Product SKU")
    product_name = fields.Char(string="Product Name")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  readonly=True)
    currency_symbol=fields.Char(string="Currency Symbol")



    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                    TRUNCATE TABLE "res_pricing_rule"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)

        company_fetch = self.env['res.company'].search([], limit=1, order="id desc")
        insert_query="""INSERT INTO res_pricing_rule(customer_name, product_code, product_name, cost,currency_id,currency_symbol) values """
        price_list=self.env.context.get('price_list')
        if price_list and  not price_list is None :
            partners = self.env['res.partner'].search([('active','=',True),('customer_rank','>',0),('is_parent','=',True)])
            for part in partners:
                if part.property_product_pricelist and part.property_product_pricelist.id in price_list:
                    product_price_list_item = self.env['product.pricelist.item'].search(
                        [('pricelist_id', '=', part.property_product_pricelist.id)])
                    product_ids=[]
                    if product_price_list_item:
                        product = product_price_list_item.mapped('product_tmpl_id.id')
                        if product:
                            product = self.env['product.product'].search(
                                [('product_tmpl_id', 'in', product)]).ids
                            product_ids.extend(product)
                        product = product_price_list_item.mapped('product_id.id')
                        if product:
                            product_ids.extend(product)
                    products = self.env['product.product'].search(
                        [('id', 'in', product_ids)])
                    i=0
                    pricelist = self.env['product.pricelist']
                    for product in products:
                        product_price = part.property_product_pricelist._get_product_price(product, 1.0)
                        # product_price = 1.2
                        values="(%s,%s,%s,%s,%s,%s)"
                        final_query=insert_query + " " + values
                        # self._cr.execute(final_query,(str(part.display_name),
                        #                               str(product.product_tmpl_id.sku_code),
                        #                               str(product.product_tmpl_id.name),
                        #                               str(product_price),
                        #                               str(product.product_tmpl_id.company_id.currency_id.id),
                        #                               str(product.product_tmpl_id.company_id.currency_id.symbol)))
                        self._cr.execute(final_query,(str(part.display_name),
                                                      str(product.product_tmpl_id.sku_code),
                                                      str(product.product_tmpl_id.name),
                                                      str(product_price),
                                                      company_fetch.currency_id.id,
                                                      company_fetch.currency_id.symbol
                                                      ))

    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

