# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr

_logger = logging.getLogger(__name__)


class sps_recieving_list(models.Model):
    _inherit = 'stock.picking'

    sku = fields.Char('Product SKU', store=False, compute="_findSKU")
    p_name = fields.Char('Product Name', store=False)
    lot_no = fields.Char('Lot No#', store=False)
    exp_date = fields.Date('Exp Date', store=False)
    qty_recieved = fields.Integer('Qty Recieved', store=False)
    uom=fields.Char('UOM', store=False)

    @api.multi
    def _findSKU(self):
        sorted = self.env['stock.picking'].search([('state', '=', 'done')])

        for order in self:
            delivery_packaging_ids1 = self.env['stock.move.line'].search([('state','=','done')])
            for p in delivery_packaging_ids1:
                order.lot_no = p.lot_id.name
                order.uom = p.product_uom_id.name

                for p1 in sorted:
                    order.sku = p1.product_id.product_tmpl_id.sku_code
                    order.p_name = p1.product_id.product_tmpl_id.name

                    for d in order.delivery_packaging_ids:
                        order.qty_recieved=d.qty
