# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class ProductSaleByCount(models.Model):
    _inherit = "product.product"

    sku_name = fields.Char("Product ",store=False)
    product_name = fields.Char("Product Name ", store=False)
    total_sale_qty = fields.Float("Quantity", compute='_compare_data', store=False)

    def _compare_data(self):
        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')

        if start_date is None:
            start_date = (fields.date.today() - datetime.timedelta(days=30))
        else:
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT).date()

        if end_date is None:
            end_date = (fields.date.today())
        else:
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT).date()

        sale_orders = self.env['sale.order'].search([])

        filtered_by_current_month = list(filter(
            lambda x: x.confirmation_date and fields.Datetime.from_string(x.confirmation_date).date() >= start_date and fields.Datetime.from_string(
                x.confirmation_date).date() <= end_date, sale_orders))

        order_ids =[x.id for x in filtered_by_current_month]

        sale_order_lines = self.env['sale.order.line'].search([('order_id', 'in', order_ids)])
        # products = {}
        for sale_order_line in sale_order_lines:
            product = sale_order_line.product_id
            product.total_sale_qty = product.total_sale_qty + sale_order_line.product_uom_qty
            product.sku_name = product.product_tmpl_id.sku_code
            product.product_name = product.name