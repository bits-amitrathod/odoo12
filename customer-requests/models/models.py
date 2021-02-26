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

    is_parent_assigned = fields.Boolean(store=False, compute="_get_parent_id")

    #@api.multi
    @api.depends('email')
    def _get_username(self):
        for record in self:
            record.api_username = record.email

    #@api.multi
    @api.depends('parent_id')
    @api.onchange('parent_id')
    def _get_parent_id(self):
        for record in self:
            record.is_parent_assigned = not record.parent_id.id