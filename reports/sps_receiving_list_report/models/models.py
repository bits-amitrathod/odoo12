# # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SpsReceivingList(models.Model):
    _inherit = 'stock.move.line'

    sku_code = fields.Char('Product SKU', store=False, compute="_get_sku")
    qty_rece = fields.Float('Qty Received', store=False, compute="_get_sku",digits=dp.get_precision('Product Unit of Measure'))

    @api.multi
    def _get_sku(self):
        for move_line in self:
            if move_line.product_id:
                move_line.sku_code = move_line.product_id.sku_code
                move_line.qty_rece=move_line.qty_done
