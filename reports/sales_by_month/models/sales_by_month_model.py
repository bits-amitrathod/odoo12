# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class ProductSaleByCount(models.Model):
    _inherit = "product.product"

    sku_name = fields.Char("Product ", compute='_compare_data', store=False)
    product_name = fields.Char("Product Name ", store=False)
    product_price = fields.Monetary(string='Price', currency_field='currency_id', store=False)
    total_sale_qty = fields.Float("Quantity", store=False)
    total_amount = fields.Monetary(string='Total', currency_field='currency_id', store=False)


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

        print(start_date)
        print(end_date)

        sale_orders = self.env['sale.order'].search([('confirmation_date', '>=', str(start_date)), ('confirmation_date', '<=', str(end_date))])
        sale_order_id_list = []
        for sale_order in sale_orders:
            sale_order_id_list.append(sale_order.id)
        print(sale_order_id_list)

        for product in self:
            product.product_name = product.product_tmpl_id.name
            product.sku_name = product.product_tmpl_id.sku_code
            sale_order_lines = self.env['sale.order.line'].search([('product_id', '=', product.id),('order_id', 'in', sale_order_id_list)])
            reserved_qty = 0
            for sale_order_line in sale_order_lines:
                product.product_price = sale_order_line.price_unit
                stock_move = self.env['stock.move'].search([('product_id', '=', sale_order_line.product_id.id), ('sale_line_id', '=', sale_order_line.id),('state', 'in', ('partially_available','done'))])
                stock_move_lines = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
                for stock_move_line in stock_move_lines:
                    reserved_qty = reserved_qty + stock_move_line.product_uom_qty

            product.total_sale_qty = reserved_qty
            product.total_amount = product.product_price * product.total_sale_qty

