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



    @api.model_cr
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
        products = self.env.context.get('product_id')
        if not customer_list is None:
            for part in customer_list:
                _logger.info("res_partner : %r", part)
                for product in products:
                    product_price = part.property_product_pricelist.get_product_price(product, 1.0, part)
                    values="(%s,%s,%s,%s,%s,%s,%s)"
                    final_query=insert_query + " " + values
                    self._cr.execute(final_query,(str(part.display_name),str(product.product_tmpl_id.sku_code),str(product.product_tmpl_id.name),str(product_price),str(product.product_tmpl_id.company_id.currency_id.id),str(product.product_tmpl_id.company_id.currency_id.symbol),str(product.product_tmpl_id.id)))

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

