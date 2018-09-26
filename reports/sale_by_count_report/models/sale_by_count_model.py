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

    @api.multi
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

        for product in self:
            sale_order_lines = self.env['sale.order.line'].search([('product_id', '=', product.id)])
            for sale_order_line in sale_order_lines:
                if sale_order_line.order_id.confirmation_date and (start_date <= fields.Datetime.from_string(
                        sale_order_line.order_id.confirmation_date).date() <= end_date):
                    product.total_sale_qty = product.total_sale_qty + sale_order_line.product_uom_qty
                    product.product_name = product.product_tmpl_id.name
                    product.sku_name = product.product_tmpl_id.sku_code
