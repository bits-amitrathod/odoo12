# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class inventory__allocation_so(models.Model):
     _name = "inventory_allocation_so.allocation_for_so"
     _auto = False
     sale_order_name = fields.Char(string="Name")
     product_id = fields.Many2one('product.product', string='Product', )
     partner_id = fields.Many2one('res.partner', string='Customer', )
     cost = fields.Float(string="Unit Price")
     product_qty = fields.Integer(string="Quantity")
     product_code = fields.Char(string="Product Code")
     product_name=fields.Char(string="Name")
     product_qty=fields.Integer(string="Product UOM Qty")

     # currency_id = fields.Many2one("res.currency", related='user_id.company_id.currency_id', string="Currency",
     #                               readonly=True)

     @api.model_cr
     def init(self):
          self.init_table()

     def init_table(self):

          tools.drop_view_if_exists(self._cr, 'allocation_for_so')
          select_query=""" SELECT so.name as sale_order_name,res.name as customer_name, sol.product_id as product_id,so.partner_id as partner_id,
          po.default_code as product_code, sol.name as product_name,sol.product_uom_qty as product_qty,sol.price_unit as cost
          from  sale_order so LEFT JOIN res_partner res ON res-id=so.partner_id LEFT JOIN sale_order_line sol ON sol.order_id=so.id LEFT JOIN product_product po ON po.id=sol.product_id LEFT JOIN stock_move sm ON sm.sale_line_id = sol.id 
          LEFT JOIN stock_move_line sml ON sml.move_id=sm.id where sm.state='assigned' and sml.state='assigned' and sml.qty_done > 0  ORDER BY so.name """



          sql_query = "CREATE VIEW allocation_for_so AS ( " + select_query  + " )"

          self._cr.execute(sql_query)

     @api.model_cr
     def delete_and_create(self):
          self.init_table()

