# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'popup.lot.history'
    lot_id = fields.Many2one('stock.production.lot', string="lot", required=True)

    def open_table(self):
        res_model = "lot.history.report"
        return self.env[res_model].with_context({'lot_id': self.lot_id.id}).delete_and_create()
