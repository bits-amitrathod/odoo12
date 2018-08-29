# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SpsCustomerUploadedDocument(models.Model):

    _name = 'sps.cust.uploaded.documents'
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    request_ids = fields.One2many('sps.customer.requests', 'document_id')
    token = fields.Char()
    document_name = fields.Char()
    file_location = fields.Char()
    source = fields.Char()
    status = fields.Char()
