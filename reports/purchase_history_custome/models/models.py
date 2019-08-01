# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class PurchaseHistory(models.Model):

    _inherit = 'purchase.order.line'



    sku = fields.Char("Product SKU", store=False, compute="_calculateSKU1")
    vendor = fields.Char("Vendor Name", store=False)
    qty = fields.Integer("Delivered Qty", store=False)
    manufacturer_rep = fields.Char("Manufacturer", store=False)
    product_name=fields.Char("Product Name", store=False)
    minExpDate = fields.Date("Min Expiration Date", store=False, compute="_calculateDate1")
    maxExpDate = fields.Date("Max Expiration Date", store=False, compute="_calculateDate2")
    unit_price=fields.Monetary("Price Per Unit", store=False)
    order_name = fields.Char("Po Name", store=False , compute="_calculateSKU1")
    date_done = fields.Date("Date Done", store=False, compute="_calculateSKU1")


    @api.multi
    def _calculateSKU1(self):
        for order in self:
            for p in order:
                order.sku = p.product_id.product_tmpl_id.sku_code
                order.vendor = p.partner_id.name
                order.manufacturer_rep = p.partner_id.name
                order.product_name = p.product_id.product_tmpl_id.name
                order.qty = p.qty_received
                order.unit_price = (float_repr(p.price_unit, precision_digits=2))
                order.order_name = order.order_id.name
                stock_picking = self.env['stock.picking'].search([('origin','like',order.order_id.name),
                                                                  ('state','=','done')], limit=1)
                order.date_done = stock_picking.date_done



    @api.onchange('minExpDate')
    def _calculateDate1(self):

        for order in self:
            print(order.product_id.id)
            if order.product_id.id!=False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = self.env.cr.dictfetchone()
                print(query_result)
                order.minExpDate = query_result['min']
                print(order.minExpDate)



    @api.onchange('maxExpDate')
    def _calculateDate2(self):
        for order in self:
            print(order.product_id.id)
            if order.product_id.id != False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                print(query_result)
                order.maxExpDate = query_result['max']
                print(order.maxExpDate)


