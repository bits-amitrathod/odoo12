# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class SalePurchaseHistory(models.Model):
    _inherit = "sale.order.line"

    # product_name = fields.Char("Product Name", compute='_compare_data',store=False)
    product_sku_ref = fields.Char("Product SKU", compute='_compare_data', store=False)
    customer_name = fields.Char("Customer Name",compute='_compare_data', store=False)
    delivered_date = fields.Date("Delivered Date",compute='_compare_data', store=False)
    # qty_delivered = fields.Float("Delivered Qty", store=False)
    # unit_price = fields.Monetary("Unit Price", currency_field='currency_id', store=False)
    # total_price = fields.Monetary("Total", currency_field='currency_id', store=False)
    # user_id = fields.Many2one('res.users', string='User', store=False)
    # currency_id = fields.Many2one("res.currency", string="Currency",readonly=True)
    # product_uom = fields.Char(string='UOM', store=False)

    @api.multi
    def _compare_data(self):
        for sale_order_line in self:
            sale_order_line.customer_name=sale_order_line.order_id.partner_id.name
            sale_order_line.product_sku_ref=sale_order_line.product_id.product_tmpl_id.sku_code
            if sale_order_line.order_id.state != 'cancel':
                stock_location=self.env['stock.location'].search([('name', '=', 'Customers')])
                if stock_location:
                    stock_picking = self.env['stock.picking'].search([('sale_id', '=', sale_order_line.order_id.id),('state', '=', 'done'),('location_dest_id','=',stock_location.id)])
                    if stock_picking:
                        for picking in stock_picking:
                            sale_order_line.delivered_date = picking.date_done

                    else:
                        sale_order_line.delivered_date = None
