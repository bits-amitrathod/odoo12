# -*- coding: utf-8 -*-

import logging

import os

from datetime import datetime

import json

import random

import string

from odoo import http, SUPERUSER_ID

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

import errno

from werkzeug import FileStorage

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)

UPLOAD_DIR = "/home/odoo/uploads/"
#path = os.path.abspath(__file__)
#dir_path = os.path.dirname(os.path.dirname(os.path.dirname(path)))
#UPLOAD_DIR =  dir_path + "/Documents/uploads/"

class FileUploadController(Controller):

    @http.route('/api/upload/', type='http', auth='public', csrf=False)
    def upload_api(self, **post):
        _logger.info("inside upload_api")
        response = None
        try:
            username = post['username']
            password = post['password']
            # template_type_from_user = post['template_type']
            file_storage = FileStorage(post['file'])
        except Exception:
            response = dict(errorCode=1, message='Bad Request')
        template_type_from_user = post.get('template_type', None)
        if response is None:
            user_api_settings = request.env['res.partner'].sudo().search(
                [('api_username', '=', username), ('api_secret', '=', password)])
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
                                                                                       uploaded_file_path,
                                                                                       template_type_from_user,
                                                                                       str(request.params['file'].filename, ''))
                _logger.info("response :%r", response)
            elif len(user_api_settings) > 1:
                response = dict(errorCode=3, message='We have found Same Email Id against multiple users.')
            else:
                response = dict(errorCode=3, message='UnAuthorized Access')

                
        if "errorCode" in response:
            # username means email Id
            if not username is None:
                print(username)
                res_partners = request.env['res.partner'].sudo().search([('email', '=', username.strip())])
                print(res_partners)
                if len(res_partners) > 1:
                    customerName = ""
                    for res_partner in res_partners:
                        if customerName == "":
                            customerName = res_partner['name']
                        else:
                            customerName = customerName + "  ,  " + res_partner['name']

            if len(res_partners) == 1:
                self.send_mail(res_partners['name'], username, str(response['message']))
            elif len(res_partners) > 1:
                self.send_mail(customerName, username, str(response['message']))
            else:
                self.send_mail('', username, str(response['message']))

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
        written = request.env['sps.template.transient'].browse(import_id).sudo().write({
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

    def send_mail(self, customerName, email, reason):
        today_date = datetime.today().strftime('%m/%d/%Y')
        template = request.env.ref('customer-requests.set_log_email').sudo()
        local_context = {'customerName': customerName, 'email': email, 'date': today_date, 'reason': reason}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True, force_send=True, )
        except:
            response = {'message': 'Unable to connect to SMTP Server'}



