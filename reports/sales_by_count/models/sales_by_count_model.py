# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class ProductSaleByCountReport(models.Model):
    _name = "report.sales.by.count"
    _description = "Product Sale ByCount Report"
    _auto = False

    sku_code = fields.Char('Product SKU')
    product_tmpl_id = fields.Many2one('product.template', "Product")
    product_uom = fields.Char(string="UOM")
    quantity = fields.Integer(string='Quantity')

    def init(self):
        self.init_table()

    def init_table(self):

        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """  
            SELECT
                ROW_NUMBER () OVER (ORDER BY product_template.name) as id, 
                public.product_template.sku_code     AS sku_code,
                public.product_template.id         AS product_tmpl_id,
                public.uom_uom.name ->> 'en_US'    AS product_uom,
                SUM(sale_order_line.qty_delivered) AS quantity
            FROM
                public.sale_order
            INNER JOIN
                public.sale_order_line
            ON
                (
                    public.sale_order.id = public.sale_order_line.order_id)
            INNER JOIN
                public.product_product
            ON
                (
                    public.sale_order_line.product_id = public.product_product.id)
            INNER JOIN
                public.product_template
            ON
                (
                    public.product_product.product_tmpl_id = public.product_template.id)
            INNER JOIN
                public.uom_uom
            ON
                (
                    public.sale_order_line.product_uom = public.uom_uom.id)
            
        """
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        compute_at = self.env.context.get('compute_at')
        user_id = self.env.context.get('user_id')

        isWhereClauseAdded = False
        if compute_at == '1':
            if start_date and not start_date is None and end_date and not end_date is None:
                select_query = select_query + " where sale_order.date_order  BETWEEN '" + str(
                    start_date) + "'" + " and '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"
                isWhereClauseAdded = True
        if user_id:
            if isWhereClauseAdded:
                select_query = select_query + " and "
            else:
                select_query = select_query + " where "
            select_query = select_query + " sale_order.user_id ='" + str(user_id) + "'"

        group_by = """
            GROUP BY
                public.product_template.sku_code,
                public.product_template.id,
                public.uom_uom.name
                """

        sql_query = select_query + group_by

        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    def delete_and_create(self):
        self.init_table()

    def string_to_date(self, date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
