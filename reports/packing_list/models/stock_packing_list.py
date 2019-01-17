from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging


from odoo import models, fields, api

_logger = logging.getLogger(__name__)
import datetime




class PricingRule(models.Model):
    _inherit="stock.picking"
    _name = "res.stock_packing_list"
    _description = "sale packing list for customer"
    _auto = False
    shipping_terms=fields.Char(string="Shipping Term")
    # name = fields.Char(string="Name")
    # state= fields.Char(string="State")
    # carrier_id=fields.Integer(string="Carrier")
    #
    # ship_to=fields.Char(string="Ship To")
    # bill_to = fields.Char(string="Bill To")
    # requested_date=fields.Char(string="Requested Date")
    # shipping_terms=fields.Char(string="Shipping Term")
    # ship_via=fields.Char(string="Ship Via")
    # order_number=fields.Char(string="Order Number")
    # carton_information=fields.Char(string="Carton Information")
    # tracking_url=fields.Char(string="Tracking Url")
    # customer_name = fields.Char(string="Name")
    # product_id = fields.Many2one('product.template', string='Product', )
    # partner_id = fields.Many2one('res.partner', string='Customer', )
    # cost = fields.Float(string="Unit Price")
    # product_code = fields.Char(string="Product Code")
    # product_name = fields.Char(string="Name")
    # currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    # currency_symbol=fields.Char(string="Currency Symbol")
    # item_description=fields.Char(string="Item Description")
    # qty_ordered=fields.Char(string="Qty Ordered")
    # qty_shipped = fields.Char(string="Qty Shipped")
    # qty_remaining=fields.Char(string="Qty Remainig")

    def _compute_so_allocation(self):
        self.so_allocation = True

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'res_stock_packing_list')
        stock_location_id = self.env['stock.location'].search([('name', '=', 'Output'), ]).id
        # sql_query = """
        #             TRUNCATE TABLE "res_stock_packing_list"
        #             RESTART IDENTITY;
        # """
        # self._cr.execute(sql_query)
        s_date = self.env.context.get('start_date')
        e_date = self.env.context.get('end_date')
        sale_number = self.env.context.get('sale_number')
        shipping_number=self.env.context.get('shipping_number')
        purchase_order = self.env.context.get('purchase_order')
        select_columns=""" SELECT column_name 
                        FROM  information_schema.columns
                        WHERE 
                          table_name   = 'stock_picking'
                          and column_name != 'id' """
        self._cr.execute(select_columns)
        columns =self._cr.fetchall()
        col=""
        for column in columns:
            for colmn in column:
                if col:
                 col=col+","+"sp."+colmn
                else:
                    col = col + "sp."+colmn
        select_query = """ SELECT  distinct sp.*,
               CASE pr.shipping_terms
                   WHEN '1'
                   THEN 'Prepaid & Billed'
                   WHEN '2'
                   THEN 'Prepaid'
                   WHEN '3'
                   THEN 'Freight Collect'
               END AS shipping_terms
               from  stock_picking sp  
                      LEFT JOIN stock_move_line sml ON sml.picking_id=sp.id
                      LEFT JOIN sale_order so ON so.id=sp.sale_id  
                      LEFT JOIN res_partner pr ON pr.id=sp.partner_id 
                      LEFT JOIN sale_order_line sol ON sol.order_id=so.id
                      LEFT JOIN product_product pp ON pp.id=sol.product_id
                      LEFT JOIN product_template pt  ON pt.id=pp.product_tmpl_id 
               where sp.state='done' and pt.type='product'
        """
        if not sale_number and not shipping_number and not purchase_order:


            if (s_date is False and e_date is False) or (s_date is None and e_date is None):
                 select_query = select_query + " " + " and FALSE"
            else:
                if s_date and (not s_date is None):
                    start_date = datetime.datetime.strptime(str(s_date), "%Y-%m-%d")
                    select_query = select_query + " and sp.write_date >='" + str(start_date) + "'"
                if e_date and (not e_date is None):
                    end_date = datetime.datetime.strptime(str(e_date), "%Y-%m-%d")
                    if (s_date and (not s_date is None)) and start_date == end_date:
                        end_date = end_date + datetime.timedelta(days=1)
                    select_query = select_query + " and sp.write_date <='" + str(end_date) + "'"
        if sale_number and not sale_number is None :
            sale_order="("
            for sale in sale_number:
                sale_order=sale_order+str(sale.id)+","
            sale_order = sale_order[:-1]
            sale_order=sale_order+")"
            select_query = select_query + """and sp.sale_id in """  + sale_order
        if shipping_number:
            select_query = select_query + " and sp.carrier_tracking_ref ='" + str(shipping_number) + "'"
        if purchase_order:
            select_query = select_query + " and so.client_order_ref ='" + str(purchase_order) + "'"
        if stock_location_id:
            select_query = select_query + " and sp.location_dest_id ='" + str(stock_location_id) + "'"



        # select_query = select_query + """ GROUP BY sp.id,so.name,pt.name,pt.sku_code,sol.product_uom_qty,sol.qty_delivered,pr.street,pr.street2,pr.zip,pr.city,st.name,co.name,so.requested_date,
        #            sp.carrier_tracking_ref,sp.carrier_tracking_ref,dc.name,shipment_address,bill_address,pr.shipping_terms,dc.delivery_type  """

        sql_query = "CREATE VIEW res_stock_packing_list AS ( " + select_query +")"
        self._cr.execute(sql_query)
    @api.model_cr
    def delete_and_create(self):
        self.init_table()

