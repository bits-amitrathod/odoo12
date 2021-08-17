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
    document_processed_count = fields.Integer(string="Document Processed Count", default=0, required=True)
    high_priority_doc_pro_count = fields.Integer(string="High Priority Document Processed Count", default=0, required=True)
    email_from = fields.Char("Email From")
    template_type = fields.Char()
    document_logs = fields.Char(string='Document Logs', default='')


