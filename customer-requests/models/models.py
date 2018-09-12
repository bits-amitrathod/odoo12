# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SpsCustomer(models.Model):

    _inherit = 'res.partner'

    file = fields.Binary()
    api_secret = fields.Char()
    api_username = fields.Char(compute="_get_username", store=True)
    document_ids = fields.One2many('sps.cust.uploaded.documents', 'customer_id')
    template_ids = fields.One2many('sps.customer.template', 'customer_id')
    sps_customer_requests = fields.One2many('sps.customer.requests', 'customer_id')

    @api.multi
    @api.depends('email')
    def _get_username(self):
        for record in self:
            record.api_username = record.email