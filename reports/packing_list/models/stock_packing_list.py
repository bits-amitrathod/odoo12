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
    _name = "res.stock_packing_list"
    _description = "sale packing list for customer"
    ship_to=fields.Char(string="Ship To")
    bill_to = fields.Char(string="Bill To")
    requested_date=fields.Char(string="Requested Date")
    shipping_terms=fields.Char(string="Shipping Term")
    ship_via=fields.Char(string="Ship Via")
    order_number=fields.Char(string="Order Number")
    carton_information=fields.Char(string="Carton Information")
    tracking_url=fields.Char(string="Tracking Url")
    customer_name = fields.Char(string="Name")
    product_id = fields.Many2one('product.template', string='Product', )
    partner_id = fields.Many2one('res.partner', string='Customer', )
    cost = fields.Float(string="Unit Price")
    product_code = fields.Char(string="Product Code")
    product_name = fields.Char(string="Name")
    currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    currency_symbol=fields.Char(string="Currency Symbol")
    item_description=fields.Char(string="Item Description")
    qty_ordered=fields.Char(string="Qty Ordered")
    qty_shipped = fields.Char(string="Qty Ordered")
    qty_remaining=fields.Char(string="Qty Remainig")

    def _compute_so_allocation(self):
        self.so_allocation = True

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                    TRUNCATE TABLE "res_stock_packing_list"
                    RESTART IDENTITY;
                """
        self._cr.execute(sql_query)
        shipping_address = self.check_isAvailable(sale.partner_id.street) + " " + self.check_isAvailable(
            sale.partner_id.street2) + " " \
                           + self.check_isAvailable(sale.partner_id.zip) + " " + self.check_isAvailable(
            sale.partner_id.city) + " " + \
                           self.check_isAvailable(sale.partner_id.state_id.name) + " " + self.check_isAvailable(
            sale.partner_id.country_id.name)
        select_query = """ SELECT sp.id,pr.shipping_terms, concat(pr.street ,' ',pr.street2,' ',pr.zip,' ',pr.city,' ',st.name,' ',co.name) as address ,
          (select concat(spr.street ,' ',spr.street2,' ',spr.zip,' ',spr.city,' ',sst.name,' ',co.name) shipment_address from res_partner spr LEFT JOIN res_country_state sst ON sst.id=spr.state_id 
          LEFT JOIN res_country sc ON sc.id=spr.country_id where spr.parent_id=pr.id and spr.type='delivery' ),
           (select concat(spr.street ,' ',spr.street2,' ',spr.zip,' ',spr.city,' ',sst.name,' ',co.name) bill_address from res_partner spr LEFT JOIN res_country_state sst ON sst.id=spr.state_id 
          LEFT JOIN res_country sc ON sc.id=spr.country_id where spr.parent_id=pr.id and spr.type='invoice' ) 
        """



        select_query = select_query + """from  stock_picking sp           
                  LEFT JOIN res_partner pr ON pr.id=sp.partner_id 
                  LEFT JOIN res_country_state st ON st.id=pr.state_id 
                  LEFT JOIN res_country co ON co.id=pr.country_id
                  where sp.state='done'  """

        if not s_date is None:
            select_query = select_query + " and sml.write_date >='" + str(s_date) + "'"

        if not e_date is None:
            select_query = select_query + " and sml.write_date <='" + str(e_date) + "'"


        insert_query="""INSERT INTO res_stock_packing_list(customer_name, product_code, product_name, cost,currency_id,currency_symbol) values """
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

