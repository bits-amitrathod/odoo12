# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class ProductsOnOrder(models.Model):
    _name = "report.products.on.order"
    _auto = False

    name = fields.Char("Order #")
    order_id = fields.Many2one('sale.order', string='Order', )
    date_ordered = fields.Datetime('Order Date')
    date_due = fields.Date('Due Date')
    qty_ordered = fields.Float("Qty Ordered")
    product_uom = fields.Many2one('product.uom', 'UOM')
    sku_code = fields.Char('Product SKU')
    qty_remaining = fields.Float("Qty Remaining")
    partner_id = fields.Many2one('res.partner', string='Customer', )
    product_id = fields.Many2one('product.product', string='Product', )

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'report_products_on_order')
        sql_query = """
                        SELECT
                            ROW_NUMBER () OVER (ORDER BY order_id) as id,
                            so.id as order_id,
                            so.name              AS name,
                            so.date_order        AS date_ordered,
                            so.confirmation_date AS date_due,
                            r.id                 AS partner_id,
                            ol.product_id        AS product_id,
                            ol.product_uom_qty   AS qty_ordered,
                            product_template.sku_code,
                            ol.product_uom,
                            (ol.product_uom_qty - ol.qty_delivered) as qty_remaining 
                        FROM
                            public.sale_order so
                        INNER JOIN
                            public.sale_order_line ol
                        ON
                            (
                                so.id = ol.order_id)
                        INNER JOIN
                            public.res_partner r
                        ON
                            (
                                so.partner_id = r.id)
                        INNER JOIN
                            public.product_product
                        ON
                            (
                                ol.product_id = public.product_product.id)
                        INNER JOIN
                            public.product_template
                        ON
                            (
                                public.product_product.product_tmpl_id = public.product_template.id)
                        WHERE
                            so.state NOT IN ('cancel', 'draft') AND so.confirmation_date IS NOT NULL
                """
        partner_id = self.env.context.get('partner_id')
        product_id = self.env.context.get('product_id')

        AND = " AND "

        if not partner_id is None:
            sql_query = sql_query + AND + " partner_id = " + str(partner_id)
            AND = " AND "

        if not product_id is None:
            sql_query = sql_query + AND + " product_id = " + str(product_id)

        self._cr.execute(" CREATE VIEW report_products_on_order AS ( " + sql_query + " )")

    @api.model_cr
    def delete_and_create(self):
        self.init_table()
