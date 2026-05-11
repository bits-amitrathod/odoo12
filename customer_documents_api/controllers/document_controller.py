# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class CustomerDocumentController(http.Controller):

    @http.route('/api/customer/documents/<int:partner_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_customer_documents(self, partner_id, **kwargs):
        """Fetch all documents (ir.attachment) linked to a customer (res.partner)."""
        try:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if not partner.exists():
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Partner with ID %s not found.' % partner_id,
                    }),
                    content_type='application/json',
                    status=404,
                )

            doc = request.env['documents.document'].sudo().search([
                ('partner_id', '=', partner_id),
                ('active', '=', True),
            ])

            documents = []
            for rec in doc:
                attachment = rec.attachment_id
                documents.append({
                    'document_id': rec.id,
                    'name': rec.name or '',
                    'type': rec.type or '',
                    'mimetype': attachment.mimetype if attachment else '',
                    'attachment_id': attachment.id if attachment else False,
                    'download_url': '/web/content/%s?download=true' % attachment.id if attachment else '',
                })

            response_data = {
                'success': True,
                'partner_id': partner.id,
                'partner_name': partner.name or '',
                'documents': documents,
            }

            return Response(
                json.dumps(response_data),
                content_type='application/json',
                status=200,
            )

        except Exception as e:
            _logger.exception("Error fetching documents for partner %s", partner_id)
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                }),
                content_type='application/json',
                status=500,
            )
