# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging
from datetime import datetime

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class OnHandByDate(models.Model):
    _name = "report.on.hand.by.date"
    _auto = False

    sku_code = fields.Char('Product SKU')
    product_name = fields.Char("Product")
    qty_done = fields.Float("Qty")
    vendor_name = fields.Char("Vendor")
    price_unit = fields.Float("Unit Price")
    asset_value = fields.Float("Assets Value")

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        report_date = self.env.context.get('report_date')
        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')
        quantities = self.env.context.get('quantities')
        product_inactive = self.env.context.get('product_inactive')
        show_cost = self.env.context.get('show_cost')
        # costing_method = self.env.context.get('costing_method')

        column = """
                purchase_order_line.id,
                product_template.sku_code,
                product_template.name AS product_name,
                stock_move_line.qty_done,
                res_partner.name     AS vendor_name
                       """

        if show_cost is not None:
            column = column + """
            ,purchase_order_line.price_unit
            ,stock_move_line.qty_done * purchase_order_line.price_unit AS asset_value
            """

        select_query = """ 
            SELECT
                """ + column + """
            FROM
                purchase_order_line
            INNER JOIN
                purchase_order
            ON
                (
                    purchase_order_line.order_id = purchase_order.id)
            INNER JOIN
                product_product
            ON
                (
                    purchase_order_line.product_id = product_product.id)
            INNER JOIN
                product_template
            ON
                (
                    product_product.product_tmpl_id = product_template.id)
            INNER JOIN
                stock_move
            ON
                (
                    purchase_order_line.id = stock_move.purchase_line_id)
            INNER JOIN
                stock_move_line
            ON
                (
                    stock_move.id = stock_move_line.move_id)
            INNER JOIN
                stock_picking
            ON
                (
                    stock_move_line.picking_id = stock_picking.id)
            INNER JOIN
                stock_location
            ON
                (
                    stock_picking.location_dest_id = stock_location.id)
            INNER JOIN
                stock_warehouse
            ON
                (
                    stock_location.id = stock_warehouse.lot_stock_id)
            INNER JOIN
                res_partner
            ON
                (
                    purchase_order.partner_id = res_partner.id)
            WHERE
                stock_picking.state = 'done' 
        """

        if report_date is not None:
            select_query = select_query + " AND purchase_order.date_order >='" + str(report_date) + "'"

        if partner_id is not None:
            select_query = select_query + " AND res_partner.id =" + str(partner_id)

        if product_id is not None:
            select_query = select_query + " AND product_product.id =" + str(product_id)

        if product_inactive is None:
            select_query = select_query + " AND product_template.active = TRUE "

        if quantities is 0:
            select_query = select_query + " AND stock_move_line.qty_done > 0 "
        elif  quantities is 2:
            select_query = select_query + " AND stock_move_line.qty_done = 0 "

        sql_query = "CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )"
        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()
