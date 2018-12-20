# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class purchase_history(models.Model):

    _inherit = 'purchase.order'



    sku = fields.Char("Product SKU", store=False, compute="_calculateSKU1")
    vendor = fields.Char("Vendor", store=False)
    qty = fields.Integer("Qty", store=False)
    manufacturer_rep = fields.Char("Manufacturer", store=False)
    product_name=fields.Char("Product Name", store=False)
    minExpDate = fields.Date("Min Exp Date", store=False, compute="_calculateDate1")
    maxExpDate = fields.Date("Max Exp Date", store=False, compute="_calculateDate2")
    unit_price=fields.Monetary("Price Per Stock", store=False)


    @api.multi
    def _calculateSKU1(self):
        for order in self:

            for p in order.order_line:
                order.sku = p.product_id.product_tmpl_id.sku_code
                order.vendor = p.partner_id.name
                order.manufacturer_rep = p.partner_id.name
                order.product_name = p.product_id.product_tmpl_id.name
                order.qty = p.product_qty
                order.unit_price = (float_repr(p.price_unit, precision_digits=2))



    @api.onchange('minExpDate')
    def _calculateDate1(self):

        for order in self:

            if order.product_id.id!=False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = self.env.cr.dictfetchone()
                order.minExpDate = query_result['min']



    @api.onchange('maxExpDate')
    def _calculateDate2(self):
        for order in self:

            if order.product_id.id != False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                order.maxExpDate = query_result['max']


