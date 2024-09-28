# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import dateutil.parser
import logging
import datetime
from odoo.tools import float_repr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class tps_report_sale(models.Model):
    _name = "total_product_sale"
    _description = "Total Product Sale"

    _auto = False

    total_sales = fields.Monetary(string='Sales', currency_field='currency_id')
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_name = fields.Char("Product Name")
    sku_code = fields.Char("Product SKU")
    start_date = fields.Date("start_date")
    end_date = fields.Date("end_date")
    _rec_name = 'product_name'


    #@api.multi
    def _compare_data(self):
        popup = self.env['tps.popup.view'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        start_date = popup.start_date
        end_date = popup.end_date
        end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d")
        end_date = end_date + datetime.timedelta(days=1)


        for product in self:
            product.product_name = product.product_tmpl_id.name
            product.sku_name = product.product_tmpl_id.sku_code
            sale_order_lines = self.env['sale.order.line'].search(
                [('product_id', '=', product.id), ('order_id.date_order', '>=', start_date),
                 ('order_id.date_order', '<=', str(end_date))])
            for sale_order_line in sale_order_lines:
                product.currency_id = sale_order_line.currency_id
                product.total_sales = product.total_sales + sale_order_line.price_total



    #  @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        view = 'total_product_sale'

        tools.drop_view_if_exists(self._cr, view)
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        if start_date is None or end_date is None:
            start_date = fields.date.today()
            end_date = fields.date.today()
        s_date = (str(start_date)).replace("/", "-")
        e_date = str(end_date).replace("/", "-")

        select_query = """ SELECT  distinct pp.id,%s as start_date , %s as end_date ,sum(sol.price_total) as total_sales,sol.currency_id,pt.sku_code, pt.name as product_name,pp.product_tmpl_id
               from  product_product pp  
                      INNER JOIN sale_order_line sol ON sol.product_id=pp.id
                      INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id
                      INNER JOIN sale_order so ON so.id=sol.order_id  
                      
               """

        start_date = datetime.datetime.strptime(str(start_date), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d")
        # if start_date == end_date:
        end_date = end_date + datetime.timedelta(days=1)

        select_query = select_query + """where so.date_order>=%s and so.date_order<=%s """ + """ group by pp.id,pt.name,sku_code,pp.product_tmpl_id,sol.currency_id"""
        sql_query = "CREATE VIEW " + view + " AS ( " + select_query + ")"
        self._cr.execute(sql_query, (str(s_date), str(e_date), str(start_date), str(end_date),))


    #  @api.model_cr
    def delete_and_create(self):
        self.init_table()

