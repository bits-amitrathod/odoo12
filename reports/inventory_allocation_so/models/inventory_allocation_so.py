# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
import logging
import datetime


_logger = logging.getLogger(__name__)


class inventory_allocation_so(models.Model):
    _inherit = "product.template"
    _name = "inventory.allocation_so"
    _auto = False
    sale_order_name = fields.Char(string="Name")
    product_id = fields.Many2one('product.product', string='Product', )
    order_id = fields.Many2one('sale.order', string='Sale', )
    partner_id = fields.Many2many('res.partner', string='Customer', )
    sale_order_line = fields.One2many('sale.order.line', string='Sales Order Line')
    cost = fields.Float(string="Cost")
    so_allocation = fields.Boolean(string="isSale", compute='_compute_so_allocation')
    product_uom =fields.Char(string="Product_UOM")
    product_code = fields.Char(string="SKU/Catalog No.")
    product_name = fields.Char(string="Product Name")
    product_quantity = fields.Integer(string="Qty")
    product_uom_qty=fields.Char(string="Qty")
    currency_id = fields.Many2one("res.currency",  string="Currency",
                                   readonly=True)
    def _compute_so_allocation(self):
        self.so_allocation = True

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):

        tools.drop_view_if_exists(self._cr, 'inventory_allocation_so')
        s_date = self.env.context.get('s_date')
        e_date = self.env.context.get('e_date')
        order_id = self.env.context.get('order_id')
        product_sku = self.env.context.get('product_sku')
        select_query = """ SELECT concat(so.name ,'-',res.display_name) as sale_order_name,sol.product_uom_qty as product_quantity,concat(sol.product_uom_qty,' ',puom.name) as product_uom_qty,curr.id as currency_id,curr.symbol as currency_symbol,puom.name as product_uom, so.id as order_id, pt.*,sol.id as sale_order_id, res.name as customer_name, sol.product_id as product_id,so.partner_id as partner_id,
          pt.sku_code as product_code, pt.name as product_name,sol.price_unit as cost """



        select_query = select_query + """from  sale_order so           
          LEFT JOIN res_partner res ON res.id=so.partner_id 
          LEFT JOIN sale_order_line sol ON sol.order_id=so.id 
          LEFT JOIN product_uom puom ON  puom.id=sol.product_uom
          LEFT JOIN product_product po ON po.id=sol.product_id 
          LEFT JOIN product_template pt ON pt.id=po.product_tmpl_id
          LEFT JOIN res_company cmpy ON cmpy.id=pt.company_id 
          LEFT JOIN res_currency curr ON curr.id=cmpy.currency_id
          LEFT JOIN stock_move sm ON sm.sale_line_id = sol.id 
          LEFT JOIN stock_move_line sml ON sml.move_id=sm.id 
          where sm.state='assigned' and sml.state='assigned' and sml.qty_done > 0  """

        if order_id and not order_id is None:
            select_query = select_query + " and so.id=" + str(order_id.id)

        if s_date and not s_date is None:
            start_date = datetime.datetime.strptime(str(s_date), "%Y-%m-%d")
            select_query = select_query + " and sml.write_date >='" + str(start_date) + "'"

        if e_date and not e_date is None:
            end_date = datetime.datetime.strptime(str(e_date), "%Y-%m-%d")
            if (s_date and (not s_date is None)) and start_date == end_date:
                end_date = end_date + datetime.timedelta(days=1)
            select_query = select_query + " and sml.write_date <='" + str(end_date) + "'"

        if product_sku :
            select_query = select_query+ "and pt.sku_code = '"+str(product_sku)+ "'"


        select_query = select_query + " ORDER BY so.name"
        sql_query = "CREATE VIEW inventory_allocation_so AS ( " + select_query + " )"

        self._cr.execute(sql_query)
        alter_temp= """ALTER TABLE inventory_allocation_so RENAME COLUMN id TO template_id; """
        self._cr.execute(alter_temp)
        alter_sol = """ALTER TABLE inventory_allocation_so RENAME COLUMN sale_order_id TO id; """
        self._cr.execute(alter_sol)
    @api.model_cr
    def delete_and_create(self):
        self.init_table()

