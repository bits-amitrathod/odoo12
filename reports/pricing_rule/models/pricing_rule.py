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
    customer_name = fields.Char(string="Name")
    product_id = fields.Many2one('product.template', string='Product', )
    partner_id = fields.Many2one('res.partner', string='Customer', )
    cost = fields.Float(string="Unit Price")
    product_code = fields.Char(string="Product Code")
    product_name = fields.Char(string="Name")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  readonly=True)
    currency_symbol=fields.Char(string="Currency Symbol")

    def _compute_so_allocation(self):
        self.so_allocation = True

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                    TRUNCATE TABLE "res_pricing_rule"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)
        insert_query="""INSERT INTO res_pricing_rule(customer_name, product_code, product_name, cost,currency_id,currency_symbol) values """
        partner=self.env.context.get('partner_id')
        products = self.env.context.get('product_id')
        if partner:
            for part in partner:
                _logger.info("res_partner : %r", part)
                for product in products:
                    product_price = part.property_product_pricelist.get_product_price(product, 1.0, part)
                    if product.product_tmpl_id.sku_code :
                        sku_code=product.product_tmpl_id.sku_code
                    else:
                        sku_code=""
                    values="(" + "'" + part.display_name +"'" +"," +"'"+sku_code+"'"+","+"'"+product.product_tmpl_id.name +"'"+","+"'"+str(product_price)+"'"+","+"'"+str(product.product_tmpl_id.company_id.currency_id.id)+"'"+ ","+"'"+str(product.product_tmpl_id.company_id.currency_id.symbol)+"'"+")"
                    final_query=insert_query + " " + values
                    self._cr.execute(final_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

