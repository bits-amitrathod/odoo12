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
    event_date = fields.Datetime(string="Event Date")
    change = fields.Integer('Change')
    lot_no = fields.Char(string="Lot #")
    vendor = fields.Char(string="Vendor / Customer Name")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    product_id = fields.Many2one('product.product', string='Product Name')
    _rec_name = 'product_id'


    def init(self):
        # self.init_table()
        pass
    def init_table(self):
        sql_query = """ 
                TRUNCATE TABLE "lot_history_report"
                RESTART IDENTITY;
            """
        self._cr.execute(sql_query)
        lot_id = self.env.context.get('lot_id')
        description = self.env.context.get('description')
        insert_start = "INSERT INTO lot_history_report" \
                       "(sku_code, description, type,event,event_date,change,lot_no,product_id"
        insert_mid = ",vendor,phone,email"
        insert_end = ") "

        where_clause = ""
        if lot_id and lot_id is not None:
            where_clause = " AND stock_lot.id=" + str(lot_id)


        if description and description is not None:
            where_clause = where_clause + " AND product_template.name  = '" + str(description) + "'"

        # -------------------- purchase ------------------------
        sql_query = insert_start + insert_mid + insert_end + """ 
                SELECT
                    product_template.sku_code,
                    product_template.name            AS description,
                    CASE  WHEN stock_picking.name LIKE 'WH/OUT%' THEN 'Purchase Return' 
                    WHEN stock_picking.name LIKE 'WH/IN%' THEN 'Receive' END AS type,
                    purchase_order.name              AS event,
                    purchase_order.date_order        AS event_date,
                    CASE  WHEN stock_picking.name LIKE 'WH/OUT%' THEN (stock_move_line.qty_done * -1) 
                    WHEN stock_picking.name LIKE 'WH/IN%' THEN (stock_move_line.qty_done )  END AS change,
                    stock_lot.name        AS lot_no,
                    stock_move_line.product_id       AS product_id,
                    res_partner.name                 AS vendor,
                    res_partner.phone,
                    res_partner.email
                    
                FROM
                    purchase_order_line
                LEFT JOIN 
                    purchase_order
                ON
                    (
                        purchase_order_line.order_id = purchase_order.id)
                LEFT JOIN
                    product_product
                ON
                    (
                        purchase_order_line.product_id = product_product.id)
                LEFT JOIN
                    product_template
                ON
                    (
                        product_product.product_tmpl_id = product_template.id)
                LEFT JOIN
                    stock_move
                ON
                    (
                        purchase_order_line.id = stock_move.purchase_line_id)
                LEFT JOIN
                    stock_move_line
                ON
                    (
                        stock_move.id = stock_move_line.move_id)
                LEFT JOIN
                    stock_lot
                ON
                    (
                        stock_move_line.lot_id = stock_lot.id)
                LEFT JOIN
                    res_partner
                ON
                    (
                        purchase_order.partner_id = res_partner.id)
                LEFT JOIN
                    stock_picking
                ON
                    (
                        stock_move_line.picking_id = stock_picking.id)
                   WHERE 1 = 1 """ + where_clause

        self._cr.execute(sql_query)

        # -------------------- Sales ------------------------
        sql_query = insert_start + insert_mid + insert_end + """
                SELECT
                    product_template.sku_code,
                    product_template.name         AS description,
                    CASE  WHEN stock_picking.name LIKE 'WH/OUT%' THEN 'Delivery-OUT' 
                    WHEN stock_picking.name LIKE 'WH/PULL%' THEN 'Delivery-PULL' 
                    WHEN stock_picking.name LIKE 'WH/PICK%' THEN 'Delivery-PICK'
                    WHEN stock_picking.name LIKE 'WH/IN%' THEN 'Sale Return'
                    END AS type,
                    sale_order.name               AS event,
                    
                    sale_order.date_order  AS event_date,
                    CASE  WHEN stock_picking.name LIKE 'WH/OUT%' THEN (stock_move_line.qty_done * -1) 
                    WHEN stock_picking.name LIKE 'WH/PULL%' THEN (stock_move_line.qty_done * -1) 
                    WHEN stock_picking.name LIKE 'WH/PICK%' THEN (stock_move_line.qty_done * -1)
                    WHEN stock_picking.name LIKE 'WH/IN%' THEN (stock_move_line.qty_done )
                    END AS change,
                    stock_lot.name     AS lot_no,
                    stock_move_line.product_id    AS product_id,
                    res_partner.name              AS vendor,
                    res_partner.phone,
                    res_partner.email                    
                FROM sale_order
                INNER JOIN sale_order_line
                ON ( sale_order.id = sale_order_line.order_id )
                INNER JOIN  product_product
                ON (  sale_order_line.product_id = product_product.id )
                INNER JOIN product_template
                ON ( product_product.product_tmpl_id = product_template.id)
                INNER JOIN stock_picking
                ON ( sale_order.id = stock_picking.sale_id)        
                INNER JOIN stock_move
                ON ( stock_picking.id = stock_move.picking_id)
               INNER JOIN stock_move_line
                ON ( stock_move.id = stock_move_line.move_id)
               INNER JOIN stock_lot
                ON ( stock_move_line.lot_id = stock_lot.id)
                INNER JOIN res_partner
                ON (  sale_order.partner_id = res_partner.id)
                WHERE 1 = 1""" + where_clause

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
                stock_lot.name as lot_no,
                stock_inventory_line.product_id as product_id
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
                stock_lot
            ON
                (
                    stock_inventory_line.prod_lot_id = stock_lot.id)
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
                stock_scrap.date_done as event_date,
                stock_scrap.scrap_qty * -1 as change,
                stock_lot.name as lot_no,
                stock_scrap.product_id as product_id
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
                stock_lot
            ON
                (
                    stock_scrap.lot_id = stock_lot.id)
            WHERE stock_scrap.state = 'done'
                                    """ + where_clause

        self._cr.execute(sql_query)

    def delete_and_create(self):
        self.init_table()
        tree_view_id = self.env.ref('lot_history.view_lot_history').id
        form_view_id = self.env.ref('lot_history.lot_history_form_view').id
        return {
            "type": "ir.actions.act_window",
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            "view_mode": "tree",
            "res_model": self._name,
            "name": "Lot History"
        }
