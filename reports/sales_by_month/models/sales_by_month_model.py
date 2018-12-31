# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class ProductSaleByCount(models.Model):
    _inherit = "product.product"
    _name = "sales_by_month"
    _auto = False

    sku_code = fields.Char("Product SKU")
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    currency_symbol = fields.Char("currency symbol")
    p_name = fields.Char("Product Name")
    product_price = fields.Monetary(string='Sales Price', currency_field='currency_id')
    total_sale_quantity = fields.Float("Sales Quantity")
    total_amount = fields.Monetary(string='Total', currency_field='currency_id')
    start_date = fields.Date("start_date")
    end_date = fields.Date("end_date")

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        view = 'sales_by_month'
        tools.drop_view_if_exists(self._cr, view)
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        s_date=""
        e_date=""
        if start_date and end_date and  not start_date is None and not end_date is None:
            s_date = (str(start_date)).replace("-", "/")
            e_date = str(end_date).replace("-", "/")

        select_query = """ SELECT Distinct pp.*,%s as start_date , %s as end_date,pt.sku_code as sku_code,pt.name as p_name,sol.price_unit as product_price,curr.id as currency_id,curr.symbol as currency_symbol,sum(sml.qty_done) as total_sale_quantity, sum(sml.qty_done) * sol.price_unit as total_amount 
                            FROM product_product pp                                  
                            INNER JOIN sale_order_line sol ON sol.product_id=pp.id
                            INNER JOIN product_template pt ON pt.id=pp.product_tmpl_id 
                            INNER JOIN sale_order so ON so.id=sol.order_id
                            INNER JOIN stock_move sm ON sm.sale_line_id=sol.id
                            INNER JOIN stock_move_line sml ON sml.move_id=sm.id
                            INNER JOIN res_company cmpy ON cmpy.id=pt.company_id 
                            INNER JOIN res_currency curr ON curr.id=cmpy.currency_id                            
                  """

        # if start_date and end_date:
        #     start_date = datetime.datedatetime.strptime(str(start_date), "%Y-%m-%d")
        #     end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d")

        if start_date  and end_date and not start_date is None and not end_date is None :
            select_query = select_query + """where sml.state in ('done','partially_available') and so.confirmation_date>=%s and so.confirmation_date<=%s group by pp.id,pt.name,pt.sku_code,sol.price_unit,curr.id,curr.symbol """
            sql_query = "CREATE VIEW " + view + " AS ( " + select_query + ")"
            self._cr.execute(sql_query, (str(s_date), str(e_date), str(start_date), str(end_date),))
        else:
            select_query = select_query + """where sml.state in ('done','partially_available')  group by pp.id,pt.name,pt.sku_code,sol.price_unit,curr.id,curr.symbol  """
            sql_query = "CREATE VIEW " + view + " AS ( " + select_query + ")"
            self._cr.execute(sql_query )

    @api.model_cr
    def delete_and_create(self):
        self.init_table()