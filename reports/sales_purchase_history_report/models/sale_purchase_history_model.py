# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class SalePurchaseHistory(models.Model):
    _inherit = "sale.order.line"

    product_name = fields.Char("Product Name", store=False)
    product_sku = fields.Char("Product SKU", compute='_compare_data', store=False)
    customer_name = fields.Char("Customer Name", store=False)
    sale_order = fields.Char("Order", store=False)
    delivered_date = fields.Date("Delivered Date", store=False)
    qty_delivered = fields.Float("Delivered Qty", store=False)
    unit_price = fields.Monetary("Unit Price", currency_field='currency_id', store=False)
    total_price = fields.Monetary("Total", currency_field='currency_id', store=False)
    # sale_order_id = fields.Many2one('sale.order', 'Sales Order', required=True, store=False)
    user_id = fields.Many2one('res.users', string='User', store=False)
    currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    product_uom_id = fields.Many2one('product.uom', 'UOM')

    @api.multi
    def _compare_data(self):
        for sale_order_line in self:
            if sale_order_line.order_id.state != 'cancel':
                sale_order_line.product_name = sale_order_line.product_id.product_tmpl_id.name
                sale_order_line.product_sku = sale_order_line.product_id.product_tmpl_id.sku_code
                sale_order_line.customer_name = sale_order_line.order_id.partner_id.name
                sale_order_line.sale_order = sale_order_line.order_id.name
                # sale_order_line.sale_order_id = sale_order_line.order_id.id
                stock_picking = self.env['stock.picking'].search([('sale_id', '=', sale_order_line.order_id.id),('state', '=', 'done')])
                if len(stock_picking) == 1:
                    stock_move_line = self.env['stock.move.line'].search([('picking_id', '=', stock_picking.id),('product_id', '=', sale_order_line.product_id.id)])
                    sale_order_line.product_uom_id = stock_move_line.product_uom_id
                    sale_order_line.qty_delivered = sale_order_line.qty_delivered
                    sale_order_line.delivered_date = stock_picking.scheduled_date
                else:
                    sale_order_line.delivered_date = None
                    sale_order_line.qty_delivered = sale_order_line.qty_delivered
                sale_order_line.unit_price = sale_order_line.price_unit
                sale_order_line.total_price = sale_order_line.qty_delivered * sale_order_line.price_unit