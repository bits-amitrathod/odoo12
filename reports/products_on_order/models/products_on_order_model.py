# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


class ProductsOnOrder(models.Model):
    _name = "products.on_order"
    _auto = False

    name = fields.Char("Order #")
    customer_name = fields.Double("Customer Name")
    date_ordered = fields.Datetime('Date')
    date_due = fields.Date('Date')
    qty_ordered = fields.Double("Qty Ordered")
    qty_remaining = fields.Double("Qty Remaning")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'event_question_report')
        sql_query = """ CREATE VIEW products_on_order AS ( SELECT so.*, c.display_name as customer_name FROM (SELECT o.id as id, o.name, SUM(l.product_uom_qty) as qty_ordered, 
            (SUM(l.product_uom_qty) - SUM(l.qty_delivered)) as qty_remaining, o.validity_date as date_due, 
            o.date_order as date_ordered FROM sale_order o INNER JOIN sale_order_line l ON o.id = l.order_id INNER JOIN res_partner r 
            ON o.partner_id = r.id GROUP BY o.id) so INNER JOIN  res_partner c ON so.id = c.id)            
        """
        self._cr.execute(sql_query)
