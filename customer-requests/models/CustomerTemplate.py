# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime

import csv

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

import os
import errno

_logger = logging.getLogger(__name__)
ATTACHMENT_DIR = "/home/asim/odoo/Documents/templates/customer/"


class CustomerTemplate(models.Model):

    _name = 'sps.customer.template'

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    file_name = fields.Char('File Name')
    non_selected_columns = fields.Char(string='Non Selected Columns')
    template_type = fields.Char(string='Template Type')
    template_status = fields.Char(string='Template Status')

    mf_customer_sku = fields.Char(string='SKU')
    mf_req_no = fields.Char(string='Requisition Number')
    mf_mfr_catalog_no = fields.Char(string='Manufacturer SKU')
    mf_required_quantity = fields.Char(string='Required Quantity')
    mf_quantity = fields.Char(string='Stock')
    mf_uom = fields.Char(string='Unit Of Measurement')
    mf_product_description = fields.Char(string='Product Name')
    mf_gl_account = fields.Char(string='GL Account')

    COL_SELECTION = []


    @staticmethod
    def _read_xls_book(book):
        sheet = book.sheet_by_index(0)
        values = []
        _logger.info('sheet.nrows %r', str(sheet.nrows))
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            _logger.info("Row........... %r", row)
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        pycompat.text_type(cell.value)
                        if is_float
                        else pycompat.text_type(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                elif cell.ctype is xlrd.XL_CELL_ERROR:
                    raise ValueError(
                        ("Error cell found while reading XLS/XLSX file: %s") %
                        xlrd.error_text_from_code.get(
                            cell.value, "unknown error code %s" % cell.value)
                    )
                else:
                    values.append(cell.value)
            break
        return values

    @staticmethod
    def _parse_csv(file_path):
        column_row = []
        try:
            with open(file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                for record in reader:
                    column_row.extend(record)
                    break
        except UnicodeDecodeError as ue:
            _logger.info(str(ue))
        return column_row

    @api.model
    def create(self, vals):
        template_type = vals['template_type']
        template_type_list = ['Inventory','Requirement']
        if template_type in template_type_list:
            try:
                file_name = vals['file_name']
                file_extension = file_name[file_name.rindex('.') + 1:]
                #path = os.path.abspath(__file__)
                #dir_path = os.path.dirname(os.path.dirname(os.path.dirname(path)))
                directory_path = ATTACHMENT_DIR + str(vals['customer_id']) + "/" + template_type + "/"
                #directory_path = dir_path+"/Documents/Template/" + str(vals['customer_id']) + "/" + template_type + "/"
                #print(dir_path)
                print(directory_path)
                if not os.path.exists(os.path.dirname(directory_path)):
                    try:
                        os.makedirs(os.path.dirname(directory_path))
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise
                myfile_path = directory_path + str(file_name)
                myfile = open(myfile_path, 'wb+')
                myfile.write(vals['template_file'])
                myfile.close()

                if file_extension == 'xls' or file_extension == 'xlsx':
                    book = xlrd.open_workbook(myfile_path)
                    self.COL_SELECTION = CustomerTemplate._read_xls_book(book)
                elif file_extension == 'csv':
                    self.COL_SELECTION = CustomerTemplate._parse_csv(myfile_path)
                vals['file_name'] = myfile_path

                template_model = super(CustomerTemplate, self).create(vals)
                selected_elements, un_selected_columns = self._get_selected_un_selected_columns(template_model)
                non_selected_columns = str(','.join(un_selected_columns))
                template_model.write(dict(non_selected_columns=non_selected_columns))
                return template_model
            except ValueError:
                return [{
                    'type': 'error',
                    'message': 'Invalid File Extension',
                    'record': False,
                }]
        else:
            return [{
                'type': 'error',
                'message': 'Invalid Template Type',
                'record': False,
            }]

    def _get_selected_un_selected_columns(self, template_model):
        selected_elements = []
        field_list = list(self.env['sps.customer.template'].fields_get().keys())
        mapping_field_list = [mapping_field for mapping_field in field_list if
                              mapping_field.startswith('mf_')]
        for mapping_field in mapping_field_list:
            selected_elements.append(getattr(template_model, mapping_field, False))
        # un_selected_columns = [key for (key, value) in self.COL_SELECTION if key not in selected_elements]
        un_selected_columns = [key for key in self.COL_SELECTION if key not in selected_elements]
        return selected_elements, un_selected_columns

    @staticmethod
    def _get_list_for_dict(current_model, vals):
        result = []
        for key, value in vals.items():
            if key and key.startswith('mf_'):
                result.append(current_model[key])
        return result

