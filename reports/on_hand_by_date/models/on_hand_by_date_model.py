# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging
from datetime import datetime
import odoo.addons.decimal_precision as dp

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)


class OnHandByDate(models.Model):
    _name = "report.on.hand.by.date"
    _description = "Report OnHand By Date"

    _auto = False

    sku_code = fields.Char('Product SKU')
    product_name = fields.Char("Product Name")
    qty_done = fields.Float("Product Qty", digits='Product Unit of Measure')
    vendor_name = fields.Char("Vendor Name")
    price_unit = fields.Float("Unit Price")
    asset_value = fields.Float("Assets Value")
    is_active = fields.Boolean("is_active")
    partner_id = fields.Integer("partner_id")
    date_order = fields.Datetime("date_order")
    warehouse_id = fields.Integer('Warehouse')
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    _rec_name = 'product_name'

    def init(self):
        self.init_table()

    def init_table(self):
        res_model = self._name.replace(".", "_")
        res_model_cost = self._name.replace(".", "_") + "_cost"

        tools.drop_view_if_exists(self._cr, res_model)
        tools.drop_view_if_exists(self._cr, res_model_cost)

        default_query = """ SELECT
                purchase_order_line.id,
                product_template.sku_code,
                product_template.name AS product_name,
                stock_move_line.qty_done,
                product_template.active as is_active,
                purchase_order.partner_id,
                purchase_order.date_order,
                stock_warehouse.id as warehouse_id,
                purchase_order_line.currency_id as currency_id,
                res_partner.name     AS vendor_name
                       """

        cost_columns = default_query + """
            ,purchase_order_line.price_unit
            ,stock_move_line.qty_done * purchase_order_line.price_unit AS asset_value
        """

        from_query = """
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

        sql_query = "CREATE VIEW " + res_model + " AS ( " + cost_columns + from_query + " )"
        self._cr.execute(sql_query)

        sql_query = "CREATE VIEW " + res_model_cost + " AS ( " + cost_columns + from_query + " )"
        self._cr.execute(sql_query)

class OnHandByDateCost(models.Model):
    _name = "report.on.hand.by.date.cost"
    _description = "Report OnHand By Date Cost"

    _inherit = 'report.on.hand.by.date'
    _auto = False

    def init(self):
        self.init_table()

    def init_table(self):
        pass
