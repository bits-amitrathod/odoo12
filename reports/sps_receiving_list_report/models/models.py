# # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SpsReceivingList(models.Model):
    _inherit = 'stock.move.line'

    sku_code = fields.Char('SKU/Catalog No', store=False, compute="_get_sku")

    @api.multi
    def _get_sku(self):
        for move_line in self:
            move_line.sku_code = move_line.product_id.sku_code
