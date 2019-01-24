# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools
import dateutil.parser
import logging
import datetime
from odoo.tools import float_repr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class tps_report_sale(models.Model):
    _inherit = "product.template"
    _name = "total_product_sale"
    _auto = False


    total_sales = fields.Monetary(string='Sales', currency_field='currency_id')
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    product_name=fields.Char("Product Name")
    sku_code = fields.Char("Product SKU")
    start_date=fields.Date("start_date")
    end_date=fields.Date("end_date")
    @api.multi
    def _compare_data(self):
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')

        for product in self:
            product.product_name = product.product_tmpl_id.name
            product.sku_name = product.product_tmpl_id.sku_code
            sale_order_lines = self.env['sale.order.line'].search([('product_id', '=', product.id),('order_id.confirmation_date', '>=', start_date),('order_id.confirmation_date','<=', end_date)])
            for sale_order_line in sale_order_lines:
                product.total_sale_qty = product.total_sale_qty + sale_order_line.product_uom_qty
                product.total_sales = product.total_sales+sale_order_line.price_unit

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        view='total_product_sale'

        tools.drop_view_if_exists(self._cr, view)
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        if  start_date is None or  end_date is None:
            start_date = fields.date.today()
            end_date = fields.date.today()
        s_date = (str(start_date)).replace("-","/")
        e_date = str(end_date).replace("-","/")

        select_query = """ SELECT  distinct pt.*,%s as start_date , %s as end_date , curr.id as currency_id,curr.symbol as currency_symbol, Round(sum(sol.price_unit),2) as total_sales, pt.name as product_name
               from  product_product pp  
                      INNER JOIN sale_order_line sol ON sol.product_id=pp.id
                      INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id
                      INNER JOIN stock_move sm ON sm.sale_line_id=sol.id
                      INNER JOIN res_company cmpy ON cmpy.id=pt.company_id 
                      INNER JOIN res_currency curr ON curr.id=cmpy.currency_id
                      INNER JOIN sale_order so ON so.id=sol.order_id  
                      
               """

        start_date= datetime.datetime.strptime(str(start_date), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d")
        if start_date == end_date:
            end_date=end_date+ datetime.timedelta(days=1)

        select_query=select_query +"""where so.confirmation_date>=%s and so.confirmation_date<=%s """ + """ group by pt.id,pt.name,curr.id,curr.symbol"""
        sql_query = "CREATE VIEW " + view + " AS ( " + select_query + ")"
        self._cr.execute(sql_query, (str(s_date),str(e_date),str(start_date),str(end_date),))





    @api.model_cr
    def delete_and_create(self):
        self.init_table()
