# -*- coding: utf-8 -*-
import logging
import random
import string
from datetime import datetime
import csv
import collections
import json
import re
import os
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

    def process_portal_document(self, user_model, uploaded_file_path, template_type_from_user, file_name, document_source='Portal'):
        _logger.info('In process_portal_document')
        if not user_model.prioritization:
            return dict(errorCode=1, message='Prioritization is Not Enabled')
        if user_model.customer_rank == 0:
            return dict(errorCode=2, message='Not a Customer')
        _logger.info('user_model.parent_id %r', user_model.parent_id.id)

        if user_model.parent_id.id:
            user_id = user_model.parent_id.id
        else:
            user_id = user_model.id

        template_type = template_type_from_user

        file_extension = uploaded_file_path[uploaded_file_path.rindex('.') + 1:]

        if file_extension == 'xls' or file_extension == 'xlsx':
            requests, file_acceptable = DocumentProcessTransientModel._parse_excel(uploaded_file_path, '',
                                                                                   '', document_source)

        if file_acceptable is None and len(requests) > 0:
            today_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            file_upload_record = dict(token=DocumentProcessTransientModel.random_string_generator(30),
                                      customer_id=user_id, template_type=template_type,
                                      document_name=file_name,
                                      file_location=uploaded_file_path, source=document_source, email_from='',
                                      status='Portal In Process',
                                      create_uid=1, create_date=today_date, write_uid=1,
                                      write_date=today_date)
            file_uploaded_record = self.env['sps.cust.uploaded.documents'].create(file_upload_record)
            document_id = file_uploaded_record.id
            if document_id is not None or document_id:
                ref = str(document_id) + "_" + file_uploaded_record.token
                response = dict(errorCode=200, message='File Uploaded Successfully')

                for req in requests:
                    if 'required_quantity' in req.keys() and not req['required_quantity'].strip().isnumeric():
                        req['required_quantity'] = '1'
                    if 'uom' in req.keys() and req['uom'] == '':
                        req['uom'] = 'EA'

                    if 'customer_sku' in req.keys():
                        customer_sku = req['customer_sku']
                        product_sku = self.get_product_sku(user_model, customer_sku)
                        products = self.get_product(product_sku, req)
                        if len(products) == 0:
                            # Check product with -E
                            _logger.info('Find product sku with -E : ' + str(product_sku))
                            products = self.get_product(product_sku + '-E', req)

                        self._create_customer_request(req, user_id, document_id, user_model, products, template_type,
                                                      today_date)
                # create sales order of product priority is 0
                self.env['process.high.priority.requests'].process_high_priority_requests(document_id, 'Portal')
                if file_uploaded_record.document_logs == 'Sales order created':
                    if file_uploaded_record.request_ids:
                        for request_id in file_uploaded_record.request_ids:
                            if request_id.sale_order_line_id:
                                for sale_order_line in request_id.sale_order_line_id:
                                    if sale_order_line.order_id and sale_order_line.order_id.id and sale_order_line.order_id.access_token:
                                        return dict(errorCode=501, message=file_uploaded_record.document_logs, orderId=sale_order_line.order_id.id, accessToken=sale_order_line.order_id.access_token)
                else:
                    document = self.env['sps.cust.uploaded.documents'].search(
                        [('id', '=', int(document_id)), ('status', '=', 'In Process')])
                    document.write({'status': 'Completed'})
                    document.write({'high_priority_doc_pro_count': 1})
                    document.write({'document_processed_count': 1})
                    if file_uploaded_record.request_ids:
                        for request_id in file_uploaded_record.request_ids:
                            request_id.write({'status': 'Unprocessed'})

                    response = dict(errorCode=500, message=file_uploaded_record.document_logs)
                # if document has all voided products then Send Email Notification to customer.
                self._all_voided_products(document_id, user_model, file_uploaded_record)
            else:
                _logger.info('file is not acceptable')
                response = dict(errorCode=12, message='Error saving document record')
        else:
            _logger.info('file is not acceptable')
            return dict(errorCode=2, message='File is not acceptable. Column name modified or data is wrong.')
        return response

    def process_document(self, user_model, uploaded_file_path, template_type_from_user, file_name, email_from, document_source='Api', ):
        if not user_model.prioritization:
            return dict(errorCode=6, message='Prioritization is Not Enabled')
        if user_model.customer_rank == 0:
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
        requests, file_acceptable = DocumentProcessTransientModel._parse_csv(uploaded_file_path, mappings, non_mapped_columns)
        if file_acceptable is not None:
            requests, file_acceptable = DocumentProcessTransientModel._parse_excel(uploaded_file_path, mappings, non_mapped_columns, document_source)

        if file_acceptable is None and len(requests) > 0:
            today_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            file_upload_record = dict(token=DocumentProcessTransientModel.random_string_generator(30),
                                      # gl_account_id=gl_account_id,
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
                    if 'required_quantity' in req.keys() and not req['required_quantity'].strip().isnumeric():
                        req['required_quantity'] = '0'
                    elif 'quantity' in req.keys() and not req['quantity'].strip().isnumeric():
                        req['quantity'] = '0'

                    if 'customer_sku' in req.keys():
                        customer_sku = req['customer_sku']
                        product_sku = self.get_product_sku(user_model, customer_sku)
                        products = self.get_product(product_sku, req)
                        if len(products) == 0:
                            # Check product with -E
                            _logger.info('Find product sku with -E : ' + str(product_sku))
                            products = self.get_product(product_sku + '-E', req)
                        self._create_customer_request(req, user_id, document_id, user_model, products, template_type, today_date)
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
                            # Check Duplicate Product
                            if len(products) > 1:
                                req.update(dict(duplicate_product=True))
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
        sps_cust_uploaded_documents = self.env['sps.cust.uploaded.documents'].search([('id', '=', document_id)])
        sps_customer_requirement_all = self.env['sps.customer.requests'].search([('document_id', '=', document_id)])
        sps_customer_requirements_all_voided = self.env['sps.customer.requests'].search([('document_id', '=', document_id), ('status', 'in', ['Voided'])])
        if len(sps_customer_requirement_all) == len(sps_customer_requirements_all_voided):
            template = self.env.ref('customer-requests.final_email_response_on_uploaded_document').sudo()
            if sps_cust_uploaded_documents.source == 'Portal':
                sps_cust_uploaded_documents.write({'document_logs': 'Unfortunately, we are currently out of stock on the products that you requested. We have documented your request on your account.'})
            if user_model.user_id and user_model.user_id.partner_id and user_model.user_id.partner_id.email and \
                    user_model.account_manager_cust and user_model.account_manager_cust.partner_id and \
                    user_model.account_manager_cust.partner_id.email:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email,
                        user_model.user_id.partner_id.email, user_model.account_manager_cust.partner_id.email, template)
            elif user_model.user_id and user_model.user_id.partner_id and user_model.user_id.partner_id.email:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email,
                                                                  user_model.user_id.partner_id.email, '', template)
            elif user_model.account_manager_cust and user_model.account_manager_cust.partner_id and \
                    user_model.account_manager_cust.partner_id.email:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email, '',
                                                                  user_model.account_manager_cust.partner_id.email, template)
            else:
                self.env['prioritization.engine.model'].send_mail(user_model.name, user_model.email, '', '', template)
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
    def _get_column_mappings(mapping_field_list, templates_list, file_path, template_type_from_user):
        column_mappings = []
        template_type = None
        non_selected_columns = []
        matched_templates = {}
        for customer_template in templates_list:
            mapped_columns = []
            for mapping_field in mapping_field_list:
                if customer_template.non_selected_columns:
                    non_selected_columns = customer_template.non_selected_columns.split(',')
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
                    matched_templates.update({template_type: [column_mappings, template_type]})
            except UnboundLocalError as ue:
                if ue:
                    _logger.info("raise error :%r", ue)
        _logger.info('template_type_from_user: %r', template_type_from_user)
        if len(matched_templates) > 1:
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
        for row in map(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        str(cell.value)
                        if is_float
                        else str(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
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
    def _parse_excel(uploaded_file_path, mappings, non_mapped_columns, document_source):
        file_acceptable = None
        requests = []
        try:
            book = xlrd.open_workbook(uploaded_file_path)
            excel_data_rows_with_columns = DocumentProcessTransientModel._read_xls_book(book, read_data=True)
            if len(excel_data_rows_with_columns) > 1:
                excel_data_rows = [excel_data_rows_with_columns[idx] for idx in
                                   range(1, len(excel_data_rows_with_columns))]
                excel_columns = excel_data_rows_with_columns[0]
                if document_source != 'Portal':
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
                else:
                    try:
                        mappings = [{'template_field': 'SKU', 'mapping_field': 'mf_customer_sku'},
                         {'template_field': 'QTY', 'mapping_field': 'mf_required_quantity'},
                         {'template_field': 'UOM', 'mapping_field': 'mf_uom'}]
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
                    except Exception as ex:
                        return dict(errorCode=15, message='Column name modified.')

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
        product_sku_lower_case = product_sku.lower()
        sql_query = """ select * from  (SELECT pt.id, regexp_replace(REPLACE(RTRIM(LTRIM(REPLACE(pt.manufacturer_pref,'0',' '))),' ','0'), '[^A-Za-z0-9.]', '','g') as manufacturer_pref_cleaned, 
                                regexp_replace(REPLACE(RTRIM(LTRIM(REPLACE(pt.sku_code,'0',' '))),' ','0'), '[^A-Za-z0-9.]', '','g') as sku_code_cleaned
                                FROM product_template pt """
        if req['uom'].lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
            sql_query = sql_query + """ INNER JOIN uom_uom uu ON pt.actual_uom = uu.id """
        sql_query = sql_query + """ where pt.tracking != 'none' and pt.active = true """
        if req['uom'].lower().strip() in ['e', 'ea', 'eac', 'each', 'u', 'un', 'unit', 'unit(s)']:
            sql_query = sql_query + """ and uu.name in ('Each', 'Unit') """
        sql_query = sql_query + """ ) as temp_data where lower(sku_code_cleaned) ='""" + product_sku_lower_case + """' or lower(manufacturer_pref_cleaned) = '""" + product_sku_lower_case + """' """
        self.env.cr.execute(sql_query)
        products = self.env.cr.dictfetchall()
        # return product object
        return products

    @staticmethod
    def cleaning_code(product_sku):
        return re.sub(r'[^A-Za-z0-9.]', '', product_sku.strip("0"))
