# -*- coding: utf-8 -*-
from builtins import str

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class LotHistory(models.Model):
    _name = "lot.history.report"
    _description = "report product activity report"

    sku_code = fields.Char('Product SKU')
    description = fields.Char('Product Name')
    type = fields.Char('Type')
    event = fields.Char('Event')
    event_date = fields.Date(string="Event Date")
    change = fields.Integer('Change')
    lot_no = fields.Char(string="Lot #")
    vendor = fields.Char(string="Vendor Name")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    def init(self):
        self.init_table()

    def init_table(self):
        sql_query = """ 
                TRUNCATE TABLE "lot_history_report"
                RESTART IDENTITY;
            """
        self._cr.execute(sql_query)
        lot_id = self.env.context.get('lot_id')
        sku_code = self.env.context.get('sku_code')
        insert_start = "INSERT INTO lot_history_report" \
                       "(sku_code, description, type,event,event_date,change,lot_no"
        insert_mid = ",vendor,phone,email"
        insert_end = ") "

        where_clause = ""
        if not lot_id is None:
            where_clause = " AND stock_production_lot.id=" + str(lot_id)

        if not sku_code is None:
            where_clause = where_clause + " AND product_template.sku_code ilike '%" + str(sku_code) + "%'"

        # -------------------- purchase ------------------------
        sql_query = insert_start + insert_mid + insert_end + """ 
                SELECT
                    product_template.sku_code,
                    product_template.name            AS description,
                    'Receive'                               AS type,
                    purchase_order.name              AS event,
                    purchase_order.date_order        AS event_date,
                    stock_move_line.qty_done         AS change,
                    stock_production_lot.name        AS lot_no,
                    res_partner.name                 AS vendor,
                    res_partner.phone,
                    res_partner.email
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
                LEFT OUTER JOIN
                    stock_production_lot
                ON
                    (
                        stock_move_line.lot_id = stock_production_lot.id)
                INNER JOIN
                    res_partner
                ON
                    (
                        purchase_order_line.partner_id = res_partner.id)
                INNER JOIN
                    stock_picking
                ON
                    (
                        stock_move_line.picking_id = stock_picking.id)
                    """ + where_clause

        self._cr.execute(sql_query)

        # -------------------- Sales ------------------------
        sql_query = insert_start + insert_mid + insert_end + """
                SELECT
                    product_template.sku_code,
                    product_template.name         AS description,
                    'Ship'                               AS type,
                    sale_order.name               AS event,
                    sale_order.confirmation_date  AS event_date,
                    stock_move_line.qty_done      AS change,
                    stock_production_lot.name     AS lot_no,
                    res_partner.name              AS vendor,
                    res_partner.phone,
                    res_partner.email
                FROM
                    sale_order
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
                    stock_production_lot
                ON
                    (
                        stock_move_line.lot_id = stock_production_lot.id)
                INNER JOIN
                    res_partner
                ON
                    (
                        sale_order_line.order_partner_id = res_partner.id)
                INNER JOIN
                    stock_picking
                ON
                    (
                        stock_move_line.picking_id = stock_picking.id)
                            """ + where_clause

        self._cr.execute(sql_query)

        # -------------------- Stock ------------------------
        sql_query = insert_start + insert_end + """
            SELECT
                product_template.sku_code,
                product_template.name as description,
                'Inventory Adjustments' AS type,
                stock_inventory.name as event,
                stock_inventory.date as event_date,
                stock_inventory_line.product_qty as change,
                stock_production_lot.name as lot_no
            FROM
                stock_inventory_line
            INNER JOIN
                stock_inventory
            ON
                (
                    stock_inventory_line.inventory_id = stock_inventory.id)
            INNER JOIN
                product_product
            ON
                (
                    stock_inventory_line.product_id = product_product.id)
            INNER JOIN
                product_template
            ON
                (
                    product_product.product_tmpl_id = product_template.id)
            INNER JOIN
                stock_production_lot
            ON
                (
                    stock_inventory_line.prod_lot_id = stock_production_lot.id)
            WHERE stock_inventory.state = 'done'
                            """ + where_clause

        self._cr.execute(sql_query)

        # -------------------- Srcap ------------------------
        sql_query = insert_start + insert_end + """
            SELECT
                product_template.sku_code,
                product_template.name as description,
                'Adjustment Scrap' as type,
                stock_scrap.name as event,
                stock_scrap.date_expected as event_date,
                stock_scrap.scrap_qty * -1 as change,
                stock_production_lot.name as lot_no
            FROM
                product_product
            INNER JOIN
                product_template
            ON
                (
                    product_product.product_tmpl_id = product_template.id)
            INNER JOIN
                stock_scrap
            ON
                (
                    product_product.id = stock_scrap.product_id)
            INNER JOIN
                res_users
            ON
                (
                    stock_scrap.write_uid = res_users.id)
            INNER JOIN
                res_partner
            ON
                (
                    res_users.partner_id = res_partner.id)
            INNER JOIN
                stock_production_lot
            ON
                (
                    stock_scrap.lot_id = stock_production_lot.id)
            WHERE stock_scrap.state = 'done'
                                    """ + where_clause

        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()

        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "res_model": self._name,
            "name": "Lot History"
        }
