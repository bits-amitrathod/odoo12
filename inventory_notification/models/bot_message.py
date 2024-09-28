# -*- coding: utf-8 -*-
from odoo import models, fields, api


class hide_bot_message(models.AbstractModel):
    _inherit = 'mail.bot'

    def _get_answer(self, record, body, values, command=False):
        super(hide_bot_message, self)._get_answer(record, body, values, command=command)
        if self._is_bot_pinged(values):
            return None