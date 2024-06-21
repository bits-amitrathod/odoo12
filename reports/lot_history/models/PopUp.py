# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'popup.lot.history'
    lot_id = fields.Many2one('stock.lot', string="lot")
    description = fields.Many2one('product.product', string='Product SKU',
                               domain="[('active','=',True),('product_tmpl_id.type','=','product')]")

    def open_table(self):
        res_model = "lot.history.report"

        ctx = {}

        if self.lot_id:
            ctx['lot_id'] = self.lot_id.id

        if self.description:
            ctx['description'] = self.description.name


        return self.env[res_model].with_context(ctx).delete_and_create()
