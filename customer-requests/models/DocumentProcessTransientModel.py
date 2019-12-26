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

    def process_document(self, user_model, uploaded_file_path, template_type_from_user, file_name, email_from, document_source='Api'):
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
        mappings, template_type = DocumentProcessTransientModel._get_column_mappings(
            mapping_field_list,
            templates_list,
            uploaded_file_path, template_type_from_user,file_name)
        if len(mappings) == 0:
            if not template_type:
                _logger.info('-------Template mismatch------------')
                return dict(errorCode=9, message='Template mismatch')
            return dict(errorCode=4, message='Mappings Not Found')
        requests, file_acceptable = DocumentProcessTransientModel._parse_csv(uploaded_file_path, mappings)
        if file_acceptable is not None:
            requests, file_acceptable = DocumentProcessTransientModel._parse_excel(uploaded_file_path, mappings)
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
                    if 'customer_sku' in req.keys():
                        customer_sku = req['customer_sku']
                        product_sku = self.get_product_sku(user_model, customer_sku)
                        products = self.get_product(product_sku, req)
                        if len(products) == 0:
                            # Check product with -E
                            _logger.info('Find product sku with -E : ' + str(product_sku))
                            products = self.get_product(product_sku + '-E', req)
                    elif 'mfr_catalog_no' in req.keys():
                        mfr_catalog_no = req['mfr_catalog_no']
                        product_sku = self.get_product_sku(user_model, mfr_catalog_no)
                        products = self.get_product(product_sku, req)
                        if len(products) == 0:
                            # Check product with -E
                            _logger.info('Find product sku with -E : ' + str(product_sku))
                            products = self.get_product(product_sku + '-E', req)
                    self._create_customer_request(req, user_id, document_id, user_model, products, template_type, today_date)
                # if document has all voided products then Send Email Notification to customer.
                self._all_voided_products(document_id, user_model, file_uploaded_record)
            else:
                _logger.info('file is not acceptable')
                response = dict(errorCode=12, message='Error saving document record')
        else:
            _logger.info('file is not acceptable')
            response = dict(errorCode=2, message='Invalid File extension')
        return response

    def _create_customer_request(self, req, user_id, document_id, user_model, products, template_type, today_date):
        if len(products) > 0:
            for product in products:
                product_details = self.env['product.product'].search([('product_tmpl_id', '=', product.get('id'))])
                if len(product_details) == 1:
                    product_id = product_details.id
                    product_template_id = product_details.product_tmpl_id.id
                    if product_id != 0 and product_template_id != 0:
                        insert_data_flag = self._get_product_level_setting(req, user_id, product_id, user_model)
                        if req:
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
                            if insert_data_flag:
                                sps_customer_request = dict(document_id=document_id, customer_id=user_id, create_uid=1, create_date=today_date, write_uid=1, write_date=today_date)
                                for key in req.keys():
                                    sps_customer_request.update({key: req[key]})
                                self.env['sps.customer.requests'].create(sps_customer_request)
        else:
            req.update(dict(product_id=None, status='Voided'))
            sps_customer_request = dict(document_id=document_id, customer_id=user_id, create_uid=1, create_date=today_date, write_uid=1, write_date=today_date)
            for key in req.keys():
                sps_customer_request.update({key: req[key]})
            self.env['sps.customer.requests'].create(sps_customer_request)

    def _get_product_level_setting(self, req, user_id, product_id, user_model):
        sps_product_setting = self.env['prioritization_engine.prioritization'].search([('customer_id', '=', user_id), ('product_id', '=', product_id)])
        if len(sps_product_setting) >= 1:
            sps_product = sps_product_setting[0]
            sps_customer_product_priority = sps_product.priority
            if sps_customer_product_priority >= 0:
                auto_allocate = sps_product.auto_allocate
                min_threshold = sps_product.min_threshold
                max_threshold = sps_product.max_threshold
                cooling_period = sps_product.cooling_period
                length_of_hold = sps_product.length_of_hold
                expiration_tolerance = sps_product.expiration_tolerance
                partial_ordering = sps_product.partial_ordering
                partial_uom = sps_product.partial_UOM
        else:
            sps_customer_product_priority = user_model.priority
            if sps_customer_product_priority >= 0:
                auto_allocate = user_model.auto_allocate
                min_threshold = user_model.min_threshold
                max_threshold = user_model.max_threshold
                cooling_period = user_model.cooling_period
                length_of_hold = user_model.length_of_hold
                expiration_tolerance = user_model.expiration_tolerance
                partial_ordering = user_model.partial_ordering
                partial_uom = user_model.partial_UOM
        if sps_customer_product_priority >= 0:
            available_qty = self.env['available.product.dict'].get_available_product_qty(user_id, product_id, expiration_tolerance)
            if available_qty is None or (available_qty is not None and int(available_qty) <= 0):
                req.update(dict(customer_request_logs='As per requested expiration tolerance product lot not available.'))
            req.update(dict(product_id=product_id, status='New', priority=sps_customer_product_priority, auto_allocate=auto_allocate,
                            min_threshold=min_threshold, max_threshold=max_threshold, cooling_period=cooling_period, length_of_hold=length_of_hold,
                            expiration_tolerance=expiration_tolerance, partial_ordering=partial_ordering, partial_UOM=partial_uom,
                            available_qty=available_qty))
            return True
        else:
            return False

    def _all_voided_products(self, document_id, user_model, file_uploaded_record):
        sps_customer_requirement_all = self.env['sps.customer.requests'].search([('document_id', '=', document_id)])
        sps_customer_requirements_all_voided = self.env['sps.customer.requests'].search([('document_id', '=', document_id), ('status', 'in', ['Voided'])])
        if len(sps_customer_requirement_all) == len(sps_customer_requirements_all_voided):
            template = self.env.ref('customer-requests.final_email_response_on_uploaded_document').sudo()
            if user_model.user_id and user_model.user_id.partner_id and user_model.user_id.partner_id.email:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email, user_model.user_id.partner_id.email, template)
            else:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email, None, template)
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
                updated_qty = product.manufacturer_uom._compute_quantity(float(req_qty), product.uom_id)
                return updated_qty
        else:
            return 0

    @staticmethod
    def _get_column_mappings(mapping_field_list, templates_list, file_path, template_type_from_user,file_name=None):

        # irattachment_obj = self.env['ir.attachment']
        column_mappings = []
        template_type = None
        columns = None
        matched_templates = {}
        for customer_template in templates_list:
            mapped_columns = []
            for mapping_field in mapping_field_list:
                if customer_template[mapping_field]:
                    mapped_columns.append(
                        dict(template_field=customer_template[mapping_field], mapping_field=mapping_field))
            selected_columns = [mapped_column['template_field'] for mapped_column in mapped_columns]
            template_column_list = selected_columns  # + non_selected_columns
            file_extension = file_path[file_path.rindex('.') + 1:]
            if file_extension == 'xls' or file_extension == 'xlsx':
                book = xlrd.open_workbook(file_path)
                columns = DocumentProcessTransientModel._read_xls_book(book)[0]
            elif file_extension == 'csv':
                columns = DocumentProcessTransientModel._read_columns_from_csv(file_path)
            try:
                if all(elem in columns for elem in template_column_list):
                    column_mappings = mapped_columns
                    template_type = customer_template.template_type
                    print('template_type *')
                    print(template_type)
                    matched_templates.update({template_type: [column_mappings, template_type]})
            except UnboundLocalError as ue:
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
        return column_mappings, template_type

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
    def _parse_csv(uploaded_file_path, mappings):
        file_acceptable = None
        requests = []
        try:
            with open(uploaded_file_path) as csvfile:
                reader = csv.DictReader(csvfile)
                for record in reader:
                    x = {}
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
    def _parse_excel(uploaded_file_path, mappings):
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
                    x = {}
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

    def get_product(self, product_sku, req):
        product_sku = DocumentProcessTransientModel.cleaning_code(product_sku)
        _logger.info('product sku %r', product_sku)
        sql_query = """ select * from  (SELECT pt.id, regexp_replace(REPLACE(RTRIM(LTRIM(REPLACE(pt.manufacturer_pref,'0',' '))),' ','0'), '[^A-Za-z0-9.]', '','g') as manufacturer_pref_cleaned, 
                                regexp_replace(REPLACE(RTRIM(LTRIM(REPLACE(pt.sku_code,'0',' '))),' ','0'), '[^A-Za-z0-9.]', '','g') as sku_code_cleaned
                                FROM product_template pt """
        if req['uom'].lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
            sql_query = sql_query + """ INNER JOIN uom_uom uu ON pt.actual_uom = uu.id """
        sql_query = sql_query + """ where pt.tracking != 'none' and pt.active = true """
        if req['uom'].lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
            sql_query = sql_query + """ and uu.name in ('Each', 'Unit') """
        sql_query = sql_query + """ ) as temp_data where lower(sku_code_cleaned) ='""" + product_sku.lower() + """' or lower(manufacturer_pref_cleaned) = '""" + product_sku.lower() + """' """
        self.env.cr.execute(sql_query)
        products = self.env.cr.dictfetchall()
        # return product object
        return products

    @staticmethod
    def cleaning_code(product_sku):
        return re.sub(r'[^A-Za-z0-9.]', '', product_sku.strip("0"))