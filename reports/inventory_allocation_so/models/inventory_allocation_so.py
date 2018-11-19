# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class inventory_allocation_so(models.Model):
    _inherit = "product.template"
    _name = "inventory.allocation_so"
    _auto = False
    sale_order_name = fields.Char(string="Name")
    product_id = fields.Many2one('product.product', string='Product', )
    order_id = fields.Many2one('sale.order', string='Sale', )
    partner_id = fields.Many2one('res.partner', string='Customer', )
    sale_order_line = fields.One2many('sale.order.line', string='Sales Order Line')
    cost = fields.Float(string="Unit Price")
    so_allocation = fields.Boolean(string="isSale", compute='_compute_so_allocation')

    product_code = fields.Char(string="Product Code")
    product_name = fields.Char(string="Name")
    product_qty = fields.Integer(string="Product UOM Qty")
    group_by = fields.Char()
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
        group_by = self.env.context.get('group_by')

        select_query = """ SELECT concat(so.name ,'-',res.display_name) as sale_order_name, curr.id as currency_id,curr.symbol as currency_symbol, so.id as order_id, pt.*,sol.id as sale_order_id, res.name as customer_name, sol.product_id as product_id,so.partner_id as partner_id,
          po.default_code as product_code, sol.name as product_name,sol.product_uom_qty as product_qty,sol.price_unit as cost """

        if not group_by is None:
            select_query = select_query + ", '" + str(group_by) + "' as group_by "

        select_query = select_query + """from  sale_order so           
          LEFT JOIN res_partner res ON res.id=so.partner_id 
          LEFT JOIN sale_order_line sol ON sol.order_id=so.id 
          LEFT JOIN product_product po ON po.id=sol.product_id 
          LEFT JOIN product_template pt ON pt.id=po.product_tmpl_id
          LEFT JOIN res_company cmpy ON cmpy.id=pt.company_id 
          LEFT JOIN res_currency curr ON curr.id=cmpy.currency_id
          LEFT JOIN stock_move sm ON sm.sale_line_id = sol.id 
          LEFT JOIN stock_move_line sml ON sml.move_id=sm.id 
          where sm.state='assigned' and sml.state='assigned' and sml.qty_done > 0  """

        if not s_date is None:
            select_query = select_query + " and sml.write_date >='" + str(s_date) + "'"

        if not e_date is None:
            select_query = select_query + " and sml.write_date <='" + str(e_date) + "'"

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

