# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self.with_context(default_customer=False)).create(vals_list)
        for user in users:
            user.partner_id.write({'customer_rank': 1})
            account_payment_term = self.env['account.payment.term'].search([('name', '=', 'Net 30'), ('active', '=', True)])
            if account_payment_term:
                user.partner_id.write({'property_payment_term_id': account_payment_term.id,
                                       'property_supplier_payment_term_id': account_payment_term.id})
        return users
