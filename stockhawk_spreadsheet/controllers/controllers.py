# -*- coding: utf-8 -*-
import odoo
import json
import logging
from odoo import fields, http
from odoo.http import request
from datetime import datetime
import os
import re
import errno
import xlsxwriter
import requests
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)
ATTACHMENT_DIR = "/home/odoo/Documents/templates/customer/"


class StockhawkSpreadsheet(http.Controller):

    @http.route(['/spreadsheet/stockhawk_spreadsheet'], type='http', auth="public", website=True)
    def stockhawk_spreadsheet(self):
        print('In stockhawk_spreadsheet')
        if request.session.uid:
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            if user and user.partner_id and user.partner_id.id:
                return http.request.render('stockhawk_spreadsheet.stockhawk_spreadsheet_view')

    @http.route(['/spreadsheet/stockhawk_submission'], type='http', auth="public", website=True)
    def stockhawk_submission(self):
        return http.request.render('stockhawk_spreadsheet.stockhawk_spreadsheet_submitted')

    @http.route(['/spreadsheet/process_data'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def process_data(self, **post):
        print('In process_data')
        data = json.loads(request.httprequest.data)

        if data is not None:
            if request.session.uid:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                if user and user.partner_id and user.partner_id.active and user.partner_id.id:
                    customer_id = user.partner_id.id
                    print(customer_id)
                    users_model = request.env['res.partner'].sudo().search([("id", "=", customer_id)])
                    user_attachment_dir = ATTACHMENT_DIR + "/" + str(users_model.id) + "/Requirement/"
                    if not os.path.exists(os.path.dirname(user_attachment_dir)):
                        try:
                            os.makedirs(os.path.dirname(user_attachment_dir))
                        except OSError as exc:
                            if exc.errno != errno.EEXIST:
                                raise
                    try:
                        file_name = str('portal_' + self.cleaning_data(users_model.name) + '_' + self.cleaning_data(
                                                                  datetime.now().strftime("%d%m%Y")) + '.xlsx')
                        file_path = user_attachment_dir + file_name
                        workbook = xlsxwriter.Workbook(file_path)
                        worksheet = workbook.add_worksheet()
                        row = 0
                        while row < len(data['data']['rows']) - 1:
                            col = 0
                            while col < len(data['data']['rows'][str(row)]['cells']):
                                for key in data['data']['rows'][str(row)]['cells'][str(col)]:
                                    worksheet.write(row, col, data['data']['rows'][str(row)]['cells'][str(col)][str(key)])
                                col += 1
                            row += 1
                        workbook.close()
                    except Exception as exc:
                        _logger.error("getting error while processing document : %r", exc)

                    template_type = 'Requirement'
                    directory_path = ATTACHMENT_DIR + str(customer_id) + "/" + template_type + "/"
                    my_file_path = directory_path + file_name
                    response = request.env['sps.document.process'].sudo().process_portal_document(users_model, my_file_path,
                                                                                       template_type, file_name, 'Portal')
                    print('Response')
                    print(response)
        return {'errorCode': response['errorCode'], 'message': response['message']}

    @staticmethod
    def cleaning_data(customer_name):
        return re.sub(r'[^A-Za-z0-9.]', '', customer_name.lower().strip("0"))