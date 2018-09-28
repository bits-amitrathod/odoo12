# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)


# class ProductsOnOrder(models.Model):
#     _name = "products.on_order"
#     _auto = False
#
#     name = fields.Char("Order #")
#     customer_name = fields.Char("Customer Name")
#     date_ordered = fields.Datetime('Date')
#     date_due = fields.Date('Due Date')
#     qty_ordered = fields.Float("Qty Ordered")
#     qty_remaining = fields.Float("Qty Remaining")
#     customer_id = fields.Integer('Customer #')
#     product_id = fields.Integer('Product #')
#
#
#     @api.model_cr
#     def init(self):
#         tools.drop_view_if_exists(self._cr, 'products_on_order')
#         sql_query = """ CREATE VIEW products_on_order AS (
#         SELECT  so.*, c.display_name as customer_name, c.id as customer_id FROM (SELECT o.id as id, o.name, SUM(l.product_uom_qty) as qty_ordered, (SUM(l.product_uom_qty) - SUM(l.qty_delivered)) as qty_remaining, o.validity_date as date_due, o.date_order as date_ordered
#  FROM sale_order o INNER JOIN sale_order_line l ON o.id = l.order_id INNER JOIN res_partner r ON o.partner_id = r.id GROUP BY o.id) so INNER JOIN  res_partner c
#  ON so.id = c.id) """
#         self._cr.execute(sql_query)
#
#     @api.model_cr
#     def delete_and_create(self):
#         product_id = self.env.context.get('product_id')
#         customer_id = self.env.context.get('customer_id')
#         tools.drop_view_if_exists(self._cr, 'products_on_order')
#         if product_id is None and customer_id is None:
#             sql_query = """ CREATE VIEW products_on_order AS (
#                     SELECT  so.*, c.display_name as customer_name, c.id as customer_id FROM (SELECT o.id as id, o.name, SUM(l.product_uom_qty) as qty_ordered, (SUM(l.product_uom_qty) - SUM(l.qty_delivered)) as qty_remaining, o.validity_date as date_due, o.date_order as date_ordered
#              FROM sale_order o INNER JOIN sale_order_line l ON o.id = l.order_id INNER JOIN res_partner r ON o.partner_id = r.id GROUP BY o.id) so INNER JOIN  res_partner c
#              ON so.id = c.id) """
#         else:
#             sql_query = """ CREATE VIEW products_on_order AS (
#                                                    SELECT o.id as id, o.name, ol.product_uom_qty as qty_ordered,
#                                                  (ol.product_uom_qty - ol.qty_delivered) as qty_remaining, c.display_name as customer_name, c.id as customer_id, ol.product_id as product_id, o.validity_date as date_due, o.date_order as date_ordered
# FROM sale_order o INNER JOIN res_partner c ON o.partner_id = c.id INNER JOIN sale_order_line ol ON o.id = ol.order_id """
#             if not product_id is None:
#                 sql_query = sql_query + " WHERE ol.product_id = " + str(product_id)
#                 if not customer_id is None:
#                     sql_query = sql_query + " AND c.id = " + str(customer_id)
#             else:
#                 if not customer_id is None:
#                     sql_query = sql_query + " WHERE c.id = " + str(customer_id)
#             sql_query = sql_query + " )"
#         self._cr.execute(sql_query)




