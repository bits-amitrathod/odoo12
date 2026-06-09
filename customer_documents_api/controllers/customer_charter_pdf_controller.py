# -*- coding: utf-8 -*-

import base64
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CustomerCharterPDFController(http.Controller):

    def _json_response(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    def _validate_token(self):
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header:
            return False

        auth_header = auth_header.strip()
        if not auth_header.lower().startswith('bearer '):
            return False

        token = auth_header[7:].strip()
        configured_token = request.env['ir.config_parameter'].sudo().get_param('customer_charter.api_token')
        return bool(token) and bool(configured_token) and token == configured_token

    def _get_customer(self, customer_id):
        customer = request.env['res.partner'].sudo().browse(customer_id)
        return customer if customer.exists() else None

    def _get_customer_charter_pdfs(self, customer):
        """
        NOTE:
        This is a fallback implementation.

        TODO:
        Replace this with the real Customer Charter storage logic if your project
        stores charter documents in a dedicated model/field.

        Current logic:
        - PDFs in ir.attachment linked to res.partner
        - name/description contains 'charter'
        """
        Attachment = request.env['ir.attachment'].sudo()
        attachments = Attachment.search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', customer.id),
        ], order='id desc')

        Message = request.env['mail.message'].sudo()
        message_ids = Message.search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', customer.id),
        ]).ids
        if not message_ids:
            return attachments

        message_attachments = Attachment.search([
            ('res_model', '=', 'mail.message'),
            ('res_id', 'in', message_ids),
        ], order='id desc')
        return attachments | message_attachments

    def _get_customer_charter_pdf_by_id(self, customer, file_id):
        Attachment = request.env['ir.attachment'].sudo()
        domain = [
            ('id', '=', file_id),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', customer.id),
        ]
        return Attachment.search(domain, limit=1)

    @http.route(
        '/api/customer/<int:customer_id>/customer-charter/pdfs',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def list_customer_charter_pdfs(self, customer_id, **kwargs):
        try:
            customer = self._get_customer(customer_id)
            if not customer:
                return self._json_response({
                    'success': False,
                    'message': 'Customer not found',
                }, status=404)

            attachments = self._get_customer_charter_pdfs(customer)

            files = []
            for att in attachments:
                files.append({
                    'file_id': att.id,
                    'file_name': att.name or '',
                    'mime_type': att.mimetype or '',
                    'file_size': att.file_size or 0,
                    'download_url': '/api/customer/%s/customer-charter/pdf/%s/download' % (customer.id, att.id),
                })

            return self._json_response({
                'success': True,
                'customer_id': customer.id,
                'customer_name': customer.name or '',
                'total_files': len(files),
                'files': files,
            }, status=200)

        except Exception:
            _logger.exception('Failed to list Customer Charter PDFs for customer_id=%s', customer_id)
            return self._json_response({
                'success': False,
                'message': 'Failed to list Customer Charter PDFs',
            }, status=500)

    @http.route(
        '/api/customer/<int:customer_id>/customer-charter/pdf/<int:file_id>/download',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def download_customer_charter_pdf(self, customer_id, file_id, **kwargs):
        try:
            customer = self._get_customer(customer_id)
            if not customer:
                return self._json_response({
                    'success': False,
                    'message': 'Customer not found',
                }, status=404)

            attachment = self._get_customer_charter_pdf_by_id(customer, file_id)
            if not attachment:
                return self._json_response({
                    'success': False,
                    'message': 'PDF file not found for this customer',
                }, status=404)

            file_data = base64.b64decode(attachment.datas or b'')
            if not file_data:
                return self._json_response({
                    'success': False,
                    'message': 'File is empty',
                }, status=404)

            filename = attachment.name or ('Customer_File_%s_%s' % (customer.id, attachment.id))

            headers = [
                ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                ('Content-Length', str(len(file_data))),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ]
            return request.make_response(file_data, headers=headers)

        except Exception:
            _logger.exception(
                'Failed to download Customer Charter PDF for customer_id=%s file_id=%s',
                customer_id,
                file_id,
            )
            return self._json_response({
                'success': False,
                'message': 'Failed to download Customer Charter PDF',
            }, status=500)
