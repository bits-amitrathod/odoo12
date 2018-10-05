# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class ReturnrdSales(models.Model):
    _name = "returned_sales.order"
    _auto = False

    name = fields.Char("Order #")
    order_id = fields.Many2one('sale.order', string='Order', )
    qty_ordered = fields.Float("Qty Ordered")
    qty_remaining = fields.Float("Qty Remaining")
    partner_id = fields.Many2one('res.partner', string='Customer', )
    product_id = fields.Many2one('product.product', string='Product',)

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'returned_sales_order')
        sql_query = """ CREATE VIEW returned_sales_order AS (
                        SELECT ROW_NUMBER () OVER (ORDER BY order_id) as id, so.id as order_id, so.name as name, so.date_order as date_ordered, so.confirmation_date as date_due , r.id as partner_id, ol.product_id as product_id, ol.product_uom_qty as qty_ordered, (ol.product_uom_qty - ol.qty_delivered) as qty_remaining  FROM sale_order so INNER JOIN sale_order_line ol ON so.id = ol.order_id INNER JOIN res_partner r ON so.partner_id = r.id 
 WHERE so.state NOT IN ('cancel','draft') AND so.confirmation_date IS NOT NULL 
                """
        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')

        AND = " AND "

        if not partner_id is None:
            sql_query = sql_query + AND + " partner_id = " + str(partner_id)
            AND = " AND "

        if not product_id is None:
             sql_query = sql_query + AND + " product_id = " + str(product_id)

        sql_query = sql_query + " )"

        self._cr.execute(sql_query)

    @api.model_cr
    def delete_and_create(self):
        self.init_table()




