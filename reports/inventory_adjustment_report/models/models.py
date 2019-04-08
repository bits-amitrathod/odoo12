# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class inventory_adjustment_report(models.Model):
    _inherit = 'stock.move.line'

    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    p_sku = fields.Char("Product SKU", store=False, compute="_calculateSKU")
    p_type= fields.Char("Product Type", store=False)
    date_cal=fields.Date('Inventory Date',store=False)
    date_posted=fields.Date('Date Posted',store=False)
    amount= fields.Monetary("Unit Price", currency_field='currency_id', store=False)
    total_amt=fields.Monetary("Total",currency_field='currency_id', store=False)
    p_qty = fields.Integer('Product Qty', store=False)
    product_name = fields.Char("Product Name", store=False)
    adj_status = fields.Char("Adjustment Status", store=False)

    @api.multi
    def _calculateSKU(self):
        ACTIONS = {
            "product": "Stockable Product",
            "consu": "Consumable",
            "service": "Service",
        }

        for order in self:
            order.p_sku = order.product_id.product_tmpl_id.sku_code
            keys=order.product_id.product_tmpl_id.type
            if keys==False:
                keys = "product"
            order.p_type =(ACTIONS[keys])
            order.date_cal=order.date
            order.date_posted=order.date
            order.product_name = order.product_id.name
            order.p_qty = order.qty_done
            order.amount = (float_repr(order.product_id.product_tmpl_id.list_price, precision_digits=2))
            order.total_amt = (float_repr(order.p_qty * order.amount, precision_digits=2))
            if order.location_dest_id.name in ('Input','Stock') :
                order.adj_status = 'Inventory Adjustment'
            else:
                order.adj_status = 'Scrapped'

