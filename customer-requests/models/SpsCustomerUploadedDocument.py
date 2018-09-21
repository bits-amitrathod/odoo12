# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SpsCustomerUploadedDocument(models.Model):

    _name = 'sps.cust.uploaded.documents'
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    # template_id = fields.Many2one('sps.customer.template', string='Template')
    request_ids = fields.One2many('sps.customer.requests', 'document_id', string="Requests")
    token = fields.Char()
    document_name = fields.Char()
    file_location = fields.Char()
    source = fields.Char()
    status = fields.Char()

    template_type = fields.Char()


