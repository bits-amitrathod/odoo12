# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re
import logging

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    code = fields.Char('Delivery Carrier Code', compute="_get_code", store=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Tag code already exists !"),
    ]

    def _get_code(self):
        for record in self:
            if record.active is True:
                name = record.name.strip()
                code = re.sub(r'[\W_]+', '_', name).lower()
                record.code = code

