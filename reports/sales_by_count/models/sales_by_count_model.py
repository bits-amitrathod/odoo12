# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class ProductSaleByCountReport(models.Model):
    _name = "report.sales.by.count"
    _auto = False

    location = fields.Char(string='Location')
    user_id = fields.Many2one('res.users', 'Salesperson')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    sku_code = fields.Char('Product SKU')
    product_name = fields.Char(string='Product Name')
    quantity = fields.Char(string='Quantity')
    confirmation_date = fields.Date('Confirmation Date')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        s_date = self.env.context.get('s_date')
        e_date = self.env.context.get('e_date')

        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        select_query = """  
            SELECT
                sale_order.user_id,
                stock_move_line.id,
                sale_order.warehouse_id ,
                stock_warehouse.name || '/' || stock_location.name AS location,
                product_template.sku_code                   AS sku_code,
                product_template.name as product_name,
                sale_order.confirmation_date,
                SUM(stock_move_line.qty_done) AS quantity
            FROM
                sale_order
            INNER JOIN
                stock_warehouse
            ON
                (
                    sale_order.warehouse_id = stock_warehouse.id)
            INNER JOIN
                sale_order_line
            ON
                (
                    sale_order.id = sale_order_line.order_id)
            INNER JOIN
                product_product
            ON
                (
                    sale_order_line.product_id = product_product.id)
            INNER JOIN
                product_template
            ON
                (
                    product_product.product_tmpl_id = product_template.id)
            INNER JOIN
                stock_move
            ON
                (
                    sale_order_line.id = stock_move.sale_line_id)
            INNER JOIN
                stock_move_line
            ON
                (
                    stock_move.id = stock_move_line.move_id)
            INNER JOIN
                stock_picking
            ON
                ( stock_move_line.picking_id = stock_picking.id)
            INNER JOIN
                stock_location
            ON
                (stock_picking.location_id = stock_location.id)
        """

        where_clause = "  WHERE  sale_order.state = 'sale'"
        group_order_by = " Group by stock_warehouse.name,stock_location.name,product_template.sku_code,sale_order.confirmation_date," \
                         "product_template.name,stock_move_line.id,sale_order.user_id,sale_order.warehouse_id " \
                         "Order by location "

        sql_query = select_query + where_clause + group_order_by
        self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")

    @api.model_cr
    def delete_and_create(self):
        self.init_table()
