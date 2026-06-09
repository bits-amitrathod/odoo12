# -*- coding: utf-8 -*-

import base64
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AccountMoveDocumentsController(http.Controller):

    def _json_response(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    def _get_account_move(self, move_id):
        move = request.env['account.move'].sudo().browse(move_id)
        return move if move.exists() else None

    def _get_account_move_attachments(self, move):
        """
        Fetch all attachments (ir.attachment) linked to an account.move.
        Includes:
        - Attachments directly linked to account.move
        - Attachments linked via chatter (mail.message)
        """
        Attachment = request.env['ir.attachment'].sudo()
        attachments = Attachment.search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ], order='id desc')

        Message = request.env['mail.message'].sudo()
        message_ids = Message.search([
            ('model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ]).ids
        if not message_ids:
            return attachments

        message_attachments = Attachment.search([
            ('res_model', '=', 'mail.message'),
            ('res_id', 'in', message_ids),
        ], order='id desc')
        return attachments | message_attachments

    def _get_account_move_attachment_by_id(self, move, file_id):
        Attachment = request.env['ir.attachment'].sudo()
        domain = [
            ('id', '=', file_id),
            ('res_model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ]
        return Attachment.search(domain, limit=1)

    @http.route(
        '/api/account-move/<int:move_id>/documents',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def list_account_move_documents(self, move_id, **kwargs):
        try:
            move = self._get_account_move(move_id)
            if not move:
                return self._json_response({
                    'success': False,
                    'message': 'Account Move not found',
                }, status=404)

            attachments = self._get_account_move_attachments(move)

            files = []
            for att in attachments:
                files.append({
                    'file_id': att.id,
                    'file_name': att.name or '',
                    'mime_type': att.mimetype or '',
                    'file_size': att.file_size or 0,
                    'download_url': '/api/account-move/%s/document/%s/download' % (move.id, att.id),
                })

            return self._json_response({
                'success': True,
                'move_id': move.id,
                'move_name': move.name or '',
                'move_type': move.move_type or '',
                'partner_id': move.partner_id.id if move.partner_id else False,
                'partner_name': move.partner_id.name if move.partner_id else '',
                'total_files': len(files),
                'files': files,
            }, status=200)

        except Exception:
            _logger.exception('Failed to list Account Move documents for move_id=%s', move_id)
            return self._json_response({
                'success': False,
                'message': 'Failed to list Account Move documents',
            }, status=500)

    @http.route(
        '/api/account-move/<int:move_id>/document/<int:file_id>/download',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def download_account_move_document(self, move_id, file_id, **kwargs):
        try:
            move = self._get_account_move(move_id)
            if not move:
                return self._json_response({
                    'success': False,
                    'message': 'Account Move not found',
                }, status=404)

            attachment = self._get_account_move_attachment_by_id(move, file_id)
            if not attachment:
                return self._json_response({
                    'success': False,
                    'message': 'Document file not found for this account move',
                }, status=404)

            file_data = base64.b64decode(attachment.datas or b'')
            if not file_data:
                return self._json_response({
                    'success': False,
                    'message': 'File is empty',
                }, status=404)

            filename = attachment.name or ('AccountMove_Document_%s_%s' % (move.id, attachment.id))

            headers = [
                ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                ('Content-Length', str(len(file_data))),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ]
            return request.make_response(file_data, headers=headers)

        except Exception:
            _logger.exception(
                'Failed to download Account Move document for move_id=%s file_id=%s',
                move_id,
                file_id,
            )
            return self._json_response({
                'success': False,
                'message': 'Failed to download Account Move document',
            }, status=500)
