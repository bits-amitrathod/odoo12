# # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SpsReceivingList(models.Model):
    _inherit = 'stock.move.line'

    sku_code = fields.Char('Product SKU', store=False, compute="_get_sku")
    qty_rece = fields.Float('Qty Received', store=False, compute="_get_sku",digits=dp.get_precision('Product Unit of Measure'))
    purchase_order_id = fields.Char('Purchase Order', store=False, compute="_get_sku")
    purchase_partner_id = fields.Char('Vendor', store=False, compute="_get_sku")
    # carrier_info = fields.Integer('Carrier Info', store=False, compute="_get_sku")
    # date_order = fields.Datetime("Order Date", store=False, compute="_get_sku")
    exp_date = fields.Char('Expired Date', store=False, compute="_get_sku")


    @api.multi
    def _get_sku(self):
        for move_line in self:
            if move_line.product_id:
                purchase_order_id = move_line.move_id.purchase_line_id.order_id
                move_line.update({
                    'sku_code' :  move_line.product_id.sku_code,
                    'qty_rece' : move_line.qty_done,
                    'purchase_order_id': purchase_order_id.name ,
                    'purchase_partner_id': purchase_order_id.partner_id.name,
                    'exp_date' : move_line.lot_id.use_date
                    # 'carrier_info': purchase_order_id.carrier_info,
                    # 'date_order': purchase_order_id.date_order,
                })