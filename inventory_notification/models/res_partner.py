# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
import logging
from odoo.exceptions import ValidationError, AccessError
_logger = logging.getLogger(__name__)

class ParnerOnHoldStatus(models.Model):
    _inherit = "res.partner"

    #@api.multi
    def write(self, vals):
        #_logger.info("res.partner vals :%r",vals)
        for ml in self:
            res = super(ParnerOnHoldStatus, ml).write(vals)
            if res and ml.is_parent and 'on_hold' in vals  and not vals.get('on_hold'):
                _logger.info("on hold false: %r",vals)
                inv_notification = ml.env['inventory.notification.scheduler'].search([])
                inv_notification.process_hold_off_customer(ml)
            return res