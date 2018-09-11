# -*- coding: utf-8 -*-

import logging

import os

from datetime import datetime

import json

import random

import string

from odoo import http

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

import errno

from werkzeug import FileStorage

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)

UPLOAD_DIR = "/home/odoouser/uploads/"


class FileUploadController(Controller):

    @http.route('/api/upload/', type='http', auth='public', csrf=False)
    def upload_api(self, **post):
        response = None
        try:
            username = post['username']
            password = post['password']
            file_storage = FileStorage(post['file'])
        except Exception:
            response = dict(errorCode=1, message='Bad Request')
        if response is None:
            user_api_settings = request.env['res.partner'].sudo().search(
                [('email', '=', username), ('api_secret', '=', password)])
            if len(user_api_settings) == 1:
                user_id = user_api_settings[0].id
                directory_path = UPLOAD_DIR + str(datetime.now().strftime("%d%m%Y")) + "/" + str(user_id) + "/"
                file_name = FileUploadController.random_string_generator(10) + request.params['file'].filename
                if not os.path.exists(os.path.dirname(directory_path)):
                    try:
                        os.makedirs(os.path.dirname(directory_path))
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise
                uploaded_file_path = str(directory_path + file_name)
                file_storage.save(uploaded_file_path)
                response = request.env['sps.document.process'].sudo().process_document(user_api_settings,
                                                                                             uploaded_file_path)
            else:
                response = dict(errorCode=3, message='UnAuthorized Access')

        return json.JSONEncoder().encode(response)



    @http.route('/userslist', type='http', auth='public', csrf=False)
    def _get_users_list(self, **post):
        # cr, context, pool, uid = request.cr, request.context, request.registry, request.uid
        input_data = post['input_data']
        records = request.env['res.partner'].sudo().search([(input_data, '=', True), ('parent_id', '=', None)])
        response_data = [dict(name=record['name'], id=record['id']) for record in records]
        return str(json.dumps(response_data))

    @http.route('/template_import/set_file', methods=['POST'])
    def set_file(self, file, import_id, customer, template_type, jsonp='callback'):
        import_id = int(import_id)

        written = request.env['sps.template.transient'].browse(import_id).write({
            'file': file.read(),
            'file_name': file.filename,
            'file_type': file.content_type,
            # 'customer_id': customer
        })

        return 'window.top.%s(%s)' % (misc.html_escape(jsonp), json.dumps({'result': written}))

    @http.route('/webhook', type='json', auth='public', csrf=False, methods=["POST"], website=True)
    def test(self, **post):
        try:
            headers = request.httprequest.headers
            if headers['X-GitLab-Token'] == 'benchmark':
                _logger.info("WebHook %r", request.jsonrequest)
                os.system('sh ' + '/opt/scripts/test.sh')
                response = {'message': headers['X-GitLab-Token']}
            else:
                response = {'message': 'UnAuthorized'}
        except:
            response = {'message': 'error'}
        return json.JSONEncoder().encode(response)


    @staticmethod
    def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
