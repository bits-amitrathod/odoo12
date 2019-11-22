# -*- coding: utf-8 -*-
import logging
import random
import string
from datetime import datetime
import csv
import collections
import json
import re
try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from odoo import api, fields, models, tools, _
_logger = logging.getLogger(__name__)


class DocumentProcessTransientModel(models.TransientModel):
    _name = 'sps.document.process'

    def process_document(self, user_model, uploaded_file_path, template_type_from_user, file_name, email_from, document_source='Api', ):
        if not user_model.prioritization:
            return dict(errorCode=6, message='Prioritization is Not Enabled')
        if not user_model.customer:
            return dict(errorCode=7, message='Not a Customer')
        _logger.info('user_model.parent_id %r', user_model.parent_id.id)
        gl_account_id = None
        if user_model.parent_id.id:
            user_id = user_model.parent_id.id
            gl_account_id = user_model.id
            # return dict(errorCode=8, message='Child Customer not allowed to upload request')
        else:
            user_id = user_model.id
        mapping_field_list = list(self.env['sps.customer.template'].fields_get().keys())
        mapping_field_list = [mapping_field for mapping_field in mapping_field_list if
                              mapping_field.startswith('mf_')]
        templates_list = self.env['sps.customer.template'].search(
            [['customer_id', '=', user_id], ['template_status', '=', 'Active']])
        if len(templates_list) <= 0:
            return dict(errorCode=5, message='Template Not Found')
        mappings, non_mapped_columns, template_type = DocumentProcessTransientModel._get_column_mappings(
            mapping_field_list,
            templates_list,
            uploaded_file_path, template_type_from_user)
        if len(mappings) == 0:
            if not template_type:
                _logger.info('-------Template mismatch------------')
                return dict(errorCode=9, message='Template mismatch')
            return dict(errorCode=4, message='Mappings Not Found')
        requests, file_acceptable = DocumentProcessTransientModel._parse_csv(uploaded_file_path, mappings,
                                                                             non_mapped_columns)
        if file_acceptable is not None:
            requests, file_acceptable = DocumentProcessTransientModel._parse_excel(uploaded_file_path, mappings,
                                                                                   non_mapped_columns)
        if file_acceptable is None and len(requests) > 0:
            today_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            file_upload_record = dict(token=DocumentProcessTransientModel.random_string_generator(30),
                                      gl_account_id=gl_account_id,
                                      customer_id=user_id, template_type=template_type,
                                      document_name=file_name,
                                      file_location=uploaded_file_path, source=document_source, email_from=email_from, status='draft',
                                      create_uid=1, create_date=today_date, write_uid=1,
                                      write_date=today_date)
            file_uploaded_record = self.env['sps.cust.uploaded.documents'].create(file_upload_record)
            document_id = file_uploaded_record.id
            if document_id is not None or document_id:
                ref = str(document_id) + "_" + file_uploaded_record.token
                response = dict(message='File Uploaded Successfully', ref=ref)
                for req in requests:
                    product_id = 0
                    product_template_id = 0
                    if 'customer_sku' in req.keys():
                        customer_sku = req['customer_sku']
                        product_sku = self.get_product_sku(user_model, customer_sku)
                        product = self.get_product(product_sku)
                        if product:
                            product_id = product[0].id
                            product_template_id = product[0].product_tmpl_id.id
                    elif 'mfr_catalog_no' in req.keys():
                        mfr_catalog_no = req['mfr_catalog_no']
                        product_sku = self.get_product_sku(user_model, mfr_catalog_no)
                        product = self.get_product(product_sku)
                        if product:
                            product_id = product[0].id
                            product_template_id = product[0].product_tmpl_id.id
                    if product_id != 0 and product_template_id != 0:
                        sps_product_priotization = self.env['prioritization_engine.prioritization'].search([['customer_id', '=', user_id], ['product_id', '=', product_id]])
                        if len(sps_product_priotization) >= 1:
                            sps_product = sps_product_priotization[0]
                            sps_customer_product_priority = sps_product.priority
                        else:
                            sps_customer_product_priority = user_model.priority
                        req.update(dict(product_id=product_id, status='New', priority=sps_customer_product_priority))
                        # set uom flag, if uom_flag is false then check the partial_uom flag
                        if 'uom' in req.keys():
                            if req['uom'].lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
                                req.update(dict(uom_flag=True))
                            else:
                                req.update(dict(uom_flag=False))
                        else:
                            # Get Product UOM category id
                            product_uom_categ = self.env['uom.category'].search([('name', 'in', ['Unit', 'Each'])])
                            # get product
                            product = self.env['product.template'].search([('id', '=', product_template_id)])
                            if product.manufacturer_uom.category_id.id in product_uom_categ.ids:
                                if product.manufacturer_uom.name.lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
                                    req.update(dict(uom_flag=True))
                                else:
                                    req.update(dict(uom_flag=False))
                        # calculate product quantity
                        updated_qty = self._get_updated_qty(req, template_type, product_template_id)
                        if updated_qty != 0:
                            req.update(dict(updated_quantity=updated_qty))
                    else:
                        req.update(dict(product_id=None, status='Voided'))
                    sps_customer_request = dict(document_id=document_id, customer_id=user_id, create_uid=1, create_date=today_date, write_uid=1, write_date=today_date)
                    for key in req.keys():
                        sps_customer_request.update({key: req[key]})
                    self.env['sps.customer.requests'].create(sps_customer_request)

                # if document has all voided products then Send Email Notification to customer.
                self._all_voided_products(document_id, user_model, file_uploaded_record)
            else:
                _logger.info('file is not acceptable')
                response = dict(errorCode=12, message='Error saving document record')
        else:
            _logger.info('file is not acceptable')
            response = dict(errorCode=2, message='Invalid File extension')
        return response

    def _all_voided_products(self, document_id, user_model, file_uploaded_record):
        sps_customer_requirement_all = self.env['sps.customer.requests'].search([('document_id', '=', document_id)])
        sps_customer_requirements_all_voided = self.env['sps.customer.requests'].search([('document_id', '=', document_id), ('status', 'in', ['Voided'])])
        if len(sps_customer_requirement_all) == len(sps_customer_requirements_all_voided):
            template = self.env.ref('customer-requests.final_email_response_on_uploaded_document').sudo()
            self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email, template)
            file_uploaded_record.write({'document_processed_count': 1, 'status': 'Completed'})

    def _get_updated_qty(self, req, template_type, product_template_id):
        _logger.info('_get_updated_qty, Template type from user : ')
        _logger.info(template_type)
        if template_type.lower().strip() == "requirement":
            req_qty = req['required_quantity']
            if req['uom_flag']:
                return req_qty
            else:
                # get product
                product = self.env['product.template'].search([('id', '=', product_template_id)])
                uom = self.env['uom.uom'].search([('name', 'ilike', 'Unit'), ('category_id.id', '=', 1)])
                if len(uom) == 0:
                    uom = self.env['uom.uom'].search([('name', 'ilike', 'Each'), ('category_id.id', '=', 1)])
                updated_qty = product.manufacturer_uom._compute_quantity(float(req_qty), uom)
                return updated_qty
        else:
            return 0

    @staticmethod
    def _get_column_mappings(mapping_field_list, templates_list, file_path, template_type_from_user):
        column_mappings = []
        template_type = None
        non_selected_columns = []
        matched_templates = {}
        for customer_template in templates_list:
            if customer_template.non_selected_columns:
                non_selected_columns = customer_template.non_selected_columns.split(',')
            mapped_columns = []
            for mapping_field in mapping_field_list:
                if customer_template[mapping_field]:
                    mapped_columns.append(
                        dict(template_field=customer_template[mapping_field], mapping_field=mapping_field))
            selected_columns = [mapped_column['template_field'] for mapped_column in mapped_columns]
            template_column_list = non_selected_columns + selected_columns
            file_extension = file_path[file_path.rindex('.') + 1:]
            if file_extension == 'xls' or file_extension == 'xlsx':
                book = xlrd.open_workbook(file_path)
                columns = DocumentProcessTransientModel._read_xls_book(book)[0]
            elif file_extension == 'csv':
                columns = DocumentProcessTransientModel._read_columns_from_csv(file_path)
            compare = lambda x, y: collections.Counter(x) == collections.Counter(y)
            try:
                if compare(template_column_list, columns):
                    column_mappings = mapped_columns
                    template_type = customer_template.template_type
                    print('template_type *')
                    print(template_type)
                    matched_templates.update({template_type: [column_mappings, non_selected_columns, template_type]})
            except  UnboundLocalError as ue:
                if ue:
                    _logger.info("raise error :%r", ue)
        _logger.info('template_type_from_user: %r', template_type_from_user)
        if len(matched_templates) > 1:
            print('matched_template > 1')
            if template_type_from_user is None:
                return [], [], False
            matched_template = matched_templates.get(template_type_from_user)
            return matched_template[0], matched_template[1], matched_template[2]
        else:
            print('matched_template = 1')
        return column_mappings, non_selected_columns, template_type

    @staticmethod
    def _read_xls_book(book, read_data=False):
        sheet = book.sheet_by_index(0)
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

    @staticmethod
    def _read_columns_from_csv(file_path):
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

    @staticmethod
    def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def _parse_csv(uploaded_file_path, mappings, non_mapped_columns):
        file_acceptable = None
        requests = []
        try:
            with open(uploaded_file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                for record in reader:
                    un_mapped_data = {}
                    for non_mapped_column in non_mapped_columns:
                        if record[non_mapped_column]:
                            un_mapped_data.update(
                                {non_mapped_column: record[non_mapped_column]})
                    x = {'un_mapped_data': json.dumps(un_mapped_data)}
                    for mapping in mappings:
                        mapping_field = str(mapping['mapping_field'])
                        if mapping_field.startswith('mf_'):
                            x.update({mapping_field[3:]: record[mapping['template_field']]})
                        else:
                            x.update({mapping_field: record[mapping['template_field']]})
                    requests.append(x)
        except UnicodeDecodeError as ue:
            _logger.info(str(ue))
            file_acceptable = False
        return requests, file_acceptable

    @staticmethod
    def _parse_excel(uploaded_file_path, mappings, non_mapped_columns):
        file_acceptable = None
        requests = []
        try:
            book = xlrd.open_workbook(uploaded_file_path)
            excel_data_rows_with_columns = DocumentProcessTransientModel._read_xls_book(book, read_data=True)
            if len(excel_data_rows_with_columns) > 1:
                excel_data_rows = [excel_data_rows_with_columns[idx] for idx in
                                   range(1, len(excel_data_rows_with_columns))]
                excel_columns = excel_data_rows_with_columns[0]
                for excel_data_row in excel_data_rows:
                    un_mapped_data = {}
                    for non_mapped_column in non_mapped_columns:
                        if excel_columns.index(non_mapped_column) >= 0:
                            un_mapped_data.update(
                                {non_mapped_column: excel_data_row[excel_columns.index(non_mapped_column)]})
                    x = {'un_mapped_data': json.dumps(un_mapped_data)}
                    for mapping in mappings:
                        mapping_field = str(mapping['mapping_field'])
                        if mapping_field.startswith('mf_'):
                            x.update(
                                {mapping_field[3:]: excel_data_row[excel_columns.index(mapping['template_field'])]})
                        else:
                            x.update(
                                {mapping_field: excel_data_row[excel_columns.index(mapping['template_field'])]})
                    requests.append(x)
        except UnicodeDecodeError as ue:
            file_acceptable = False
            _logger.info(str(ue))
        return requests, file_acceptable

    @staticmethod
    def get_product_sku(user_model, sku_code):
        print('In get_product_sku()')
        customer_sku = sku_code
        product_sku = customer_sku
        sku_preconfig_flag = False
        if user_model.sku_preconfig and product_sku:
            if len(user_model.sku_preconfig) > 0:
                j = 0
                for i in user_model.sku_preconfig:
                    if user_model.sku_preconfig[j].isalnum():
                        if user_model.sku_preconfig[j] == product_sku[j]:
                            sku_preconfig_flag = True
                        else:
                            sku_preconfig_flag = False
                            break
                    j += 1
        if sku_preconfig_flag:
            product_sku = product_sku[len(user_model.sku_preconfig):]
            print('product_sku : ', product_sku)
        sku_postconfig_flag = False
        if user_model.sku_postconfig and product_sku:
            if len(user_model.sku_postconfig) > 0:
                k = -1
                for i in user_model.sku_postconfig:
                    if user_model.sku_postconfig[k].isalnum():
                        if user_model.sku_postconfig[k] == product_sku[k]:
                            sku_postconfig_flag = True
                        else:
                            sku_postconfig_flag = False
                            break
                    k -= 1
            if sku_postconfig_flag:
                product_sku = product_sku[:-len(user_model.sku_postconfig)]
        return product_sku

    def get_product(self, product_sku):
        print('In get_product()')
        product_sku = DocumentProcessTransientModel.cleaning_code(product_sku)
        _logger.info('product sku %r', product_sku)
        self.env.cr.execute("""select * from 
                                (SELECT id, regexp_replace(TRIM(LEADING '0' FROM CAST(manufacturer_pref AS TEXT)) , '[^A-Za-z0-9.]', '','g') as manufacturer_pref, 
                                regexp_replace(TRIM(LEADING '0' FROM CAST(sku_code AS TEXT)) , '[^A-Za-z0-9.]', '','g') as sku_code_cleaned
                                FROM product_template where tracking != 'none')
                                as temp_data where lower(sku_code_cleaned) ='""" + product_sku.lower() + """' or lower(manufacturer_pref) = '""" + product_sku.lower() + """' """)
        query_result = self.env.cr.dictfetchone()
        product = False
        if query_result:
            product = self.env['product.product'].search([['product_tmpl_id', '=', query_result['id']]])
            if len(product) > 0:
                product = product
            else:
                product = False
        # return product object
        return product

    @staticmethod
    def cleaning_code(str):
        return re.sub(r'[^A-Za-z0-9.]', '', str.lstrip('0'))