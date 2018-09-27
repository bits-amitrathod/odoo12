# -*- coding: utf-8 -*-

import logging

import random
import string
from datetime import datetime
import csv
import collections

import json

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

from odoo import api, fields, models, tools, _, SUPERUSER_ID

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)



class TestingController(Controller):

    @route('/api/parse', type='http', auth='public', csrf=False)
    def test_parsing(self):
        # try:
        #     uploaded_file_path = '/home/manohar/Downloads/vendor_offer.xlsx'
        #     book = xlrd.open_workbook(uploaded_file_path)
        #     excel_data_rows_with_columns = TestingController._read_xls_book(book, read_data=True)
        #     if len(excel_data_rows_with_columns) > 1:
        #         excel_data_rows = [excel_data_rows_with_columns[idx] for idx in
        #                            range(2, len(excel_data_rows_with_columns) - 1)]
        #         common_values_row = excel_data_rows_with_columns[0]
        #         _logger.info(common_values_row)
        #         excel_columns = excel_data_rows_with_columns[1]
        #         # for excel_data_row in excel_data_rows:
        #         #    _logger.info(excel_data_row)
        #     return "OK"
        # except UnicodeDecodeError as ue:
        #     _logger.info(ue)
        #     return "FALSE"
        records = request.env['sale.order.line'].sudo().search([('state', '=' , 'done')])
        return  str(records.ids)


    @staticmethod
    def _read_xls_book(book, read_data=False):
        sheet = book.sheet_by_name('PPVendorPricing')
        data = []
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        pycompat.text_type(cell.value)
                        if is_float
                        else pycompat.text_type(int(cell.value))
                    )
                # elif cell.ctype is xlrd.XL_CELL_DATE:
                #     is_datetime = cell.value % 1 != 0.0
                #     dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                #     values.append(
                #         dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                #         if is_datetime
                #         else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                #     )
                # elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                #     values.append(u'True' if cell.value else u'False')
                # elif cell.ctype is xlrd.XL_CELL_ERROR:
                #     raise ValueError(
                #         ("Error cell found while reading XLS/XLSX file: %s") %
                #         xlrd.error_text_from_code.get(
                #             cell.value, "unknown error code %s" % cell.value)
                #     )
                else:
                    values.append(cell.value)
            data.append(values)
            if not read_data:
                break
        return data

    @route('/testing', type='http', auth='public', csrf=False)
    def testing_api(self):
        res_user = request.env['res.users'].sudo().search([('id', '=', SUPERUSER_ID)])
        self.send_mail(res_user.partner_id.id, str({'message' : 'OK'}))
        return "OK " + str(SUPERUSER_ID)

    def send_mail(self, user_target, body):
        template = request.env.ref('customer-requests.set_log_email')
        local_context = {'body': body}
        template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True,force_send=True,)


