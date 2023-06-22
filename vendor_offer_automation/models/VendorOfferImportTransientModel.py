# -*- coding: utf-8 -*-
from docutils.nodes import header

from .VendorOfferAutomationTemplate import *
from datetime import datetime
import logging
import operator
import psycopg2
import itertools
import math
import base64
IMAGE_FIELDS = ["icon", "image", "logo", "picture"]
DEFAULT_IMAGE_REGEX = r"(?:http|https)://.*(?:png|jpe?g|tiff?|gif|bmp)"
import re
import requests

from odoo.tools.translate import _
from odoo.tools import config, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

FIELDS_RECURSION_LIMIT = 2
ERROR_PREVIEW_BYTES = 200

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

try:
    from . import odf_ods_reader
except ImportError:
    odf_ods_reader = None

FILE_TYPE_DICT = {
    'text/csv': ('csv', True, None),
    'application/vnd.ms-excel': ('xls', xlrd, 'xlrd'),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ('xlsx', xlsx, 'xlrd >= 1.0.0'),
    'application/vnd.oasis.opendocument.spreadsheet': ('ods', odf_ods_reader, 'odfpy')
}
EXTENSIONS = {
    '.' + ext: handler
    for mime, (ext, handler, req) in FILE_TYPE_DICT.items()
}


from odoo import models, fields, api
from odoo.exceptions import AccessError
_logger = logging.getLogger(__name__)


class VendorOfferImportTransientModel(models.TransientModel):
    _inherit = 'base_import.import'
    _name = "sps.vendor.offer.template.transient"
    # customer_id = fields.Integer('Customer')
    columns_from_template = fields.Char(string='Template Columns')

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Vendor Offer'),
            'template': '/vendor_offer_automation/static/xls/vendor_import.xlsx'
        }]

    @api.model
    def _convert_import_data(self, fields, options,import_type_ven):
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ValueError(_("You must configure at least one field to import"))
        if len(indices) == 1:
            mapper = lambda row: [row[indices[0]]]
        else:
            mapper = operator.itemgetter(*indices)
        import_fields = [f for f in fields if f]

        if 'mf_customer_sku' not in import_fields:
            raise ValueError(_("You must configure Customer SKU field to import"))

        if import_type_ven == all_field_import:
            if 'mf_quantity' not in import_fields:
                raise ValueError(_("You must configure 'Quantity' field to import"))
            if 'mf_retail_price' not in import_fields:
                raise ValueError(_("You must configure 'Retail Price' field to import"))
            if 'mf_offer_price' not in import_fields:
                raise ValueError(_("You must configure 'Offer Price' field to import"))
            if 'mf_retail_price_total' not in import_fields:
                raise ValueError(_("You must configure 'Total Retail Price' field to import"))
            if 'mf_offer_price_total' not in import_fields:
                raise ValueError(_("You must configure 'Total Offer Price' field to import"))
            if 'mf_multiplier' not in import_fields:
                raise ValueError(_("You must configure 'Multiplier' field to import"))
            if 'mf_possible_competition' not in import_fields:
                raise ValueError(_("You must configure 'Possible Competition' field to import"))
            if 'mf_accelerator' not in import_fields:
                raise ValueError(_("You must configure 'Accelerator' field to import"))


        rows_to_import = self._read_file(options)
        if options.get('headers'):
            rows_to_import = itertools.islice(rows_to_import, 0, None)
        #data = [list(row) for row in pycompat.imap(mapper, rows_to_import) if any(row)]
        data = [list(row) for row in map(mapper, rows_to_import) if any(row)]
        # if import_type_ven == 'allfieldimport':
        #     cols = data[1:2]
        #     cell_values = data[2:]
        # else:
        cols = data[0:1]
        cell_values = data[1:]
        return cell_values, import_fields, cols

    #@api.multi
    def do_custom(self, fields, columns,options, parent_model, customer_id, template_type, upload_document,offer_id, import_type_ven,dryrun=False):
        self.ensure_one()
        import_result = {'messages': []}
        try:
            self._cr.execute('SAVEPOINT import')
            data, import_fields, col = self._convert_import_data(fields, options,import_type_ven)
            # data = self._parse_import_data(parent_model,data, import_fields, options)
            if len(col) == 1:

                resource_model = self.env[parent_model]
                columns = col[0]
                dict_list = [{ import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
                resource_model_dict = dict(template_status='Active', file_name=self.file_name,
                                           columns_from_template=self.columns_from_template,
                                           customer_id=customer_id)
                for dictionary in dict_list:
                    resource_model_dict.update(dictionary)
                name_create_enabled_fields = options.pop('name_create_enabled_fields', {})

                template = resource_model.create(resource_model_dict).with_context(import_file=True,
                                                               name_create_enabled_fields=name_create_enabled_fields)
                import_result = template.load(import_fields, data)

                vendor_offer = self.env['purchase.order'].search([('id', '=', offer_id)])

                if len(vendor_offer) == 1:
                    vendor_offer[0].sudo().write({'template_id': template.id, 'document': self.file,
                                           'import_type_ven': import_type_ven})
                try:
                    if dryrun:
                        self._cr.execute('ROLLBACK TO SAVEPOINT import')
                        self.pool.reset_changes()
                    else:
                        self._cr.execute('RELEASE SAVEPOINT import')
                except psycopg2.InternalError:
                    pass
        except ValueError as error:
            _logger.info('Error %r', str(error))
            return {
                'messages': [{
                    'type': 'error',
                    'message': str(error),
                    'record': False,
                }]
            }

        # if import_result['ids'] and options.get('headers'):
        #     BaseImportMapping = self.env['base_import.mapping']
        #     for index, column_name in enumerate(columns):
        #         if column_name:
        #             # Update to latest selected field
        #             exist_records = BaseImportMapping.search([('res_model', '=', self.res_model), ('column_name', '=', column_name)])
        #             if exist_records:
        #                 exist_records.write({'field_name': fields[index]})
        #             else:
        #                 BaseImportMapping.create({
        #                     'res_model': self.res_model,
        #                     'column_name': column_name,
        #                     'field_name': fields[index]
        #                 })

        return import_result


    def _match_headers_ven(self, rows, fields, options):
        """ Attempts to match the imported model's fields to the
            titles of the parsed CSV file, if the file is supposed to have
            headers.

            Will consume the first line of the ``rows`` iterator.

            Returns the list of headers and a dict mapping cell indices
            to key paths in the ``fields`` tree. If headers were not
            requested, both collections are empty.

            :param Iterator rows:
            :param dict fields:
            :param dict options:
            :rtype: (list(str), dict(int: list(str)))
        """
        if not options.get('headers'):
            return [], {}

        headers = next(rows, None)
        if not headers:
            return [], {}

        matches = {}
        mapping_records = self.env['base_import.mapping'].search_read([('res_model', '=', self.res_model)], ['column_name', 'field_name'])
        mapping_fields = {rec['column_name']: rec['field_name'] for rec in mapping_records}
        for index, header in enumerate(headers):
            match_field = []
            mapping_field_name = mapping_fields.get(header.lower())
            if mapping_field_name:
                match_field = mapping_field_name.split('/')
            if not match_field:
                match_field = [field['name'] for field in self._match_header(header.strip(), fields, options)]
            matches[index] = match_field or None
        return headers, matches
    #@api.multi
    def parse_preview(self, options, import_type_ven, count=10):
        self.ensure_one()
        fields = self.get_fields(self.res_model,import_type_ven)
        try:
            rows = self._read_file(options)
            headers, matches = self._match_headers_ven(rows, fields, options)


            self.columns_from_template = ".".join(headers)
            preview = list(itertools.islice(rows, count))
            assert preview, "File seems to have no content"
            # header_types = self._find_type_from_preview(options, preview)
            if options.get('keep_matches', False) and len(options.get('fields', [])):
                matches = {}
                for index, match in enumerate(options.get('fields')):
                    if match:
                        matches[index] = match.split('/')

            return {
                'fields': fields,
                'matches': matches or False,
                'headers': headers or False,
                'headers_type': False,
                'preview': preview,
                'options': options,
                'debug': self.user_has_groups('base.group_no_one'),
            }
        except Exception as error:
            _logger.debug("Error during parsing preview", exc_info=True)
            preview = None
            if self.file_type == 'text/csv':
                preview = self.file[:ERROR_PREVIEW_BYTES].decode('iso-8859-1')
            return {
                'error': str(error),
                'preview': preview,
            }


    @api.model
    def _find_type_from_preview(self, options, preview):
        type_fields = []
        if preview:
            for column in range(0, len(preview[0])):
                preview_values = [value[column].strip() for value in preview]
                type_field = self._try_match_column(preview_values, options)
                type_fields.append(type_field)
        return type_fields

    @api.model
    def _try_match_column(self, preview_values, options):
        values = set(preview_values)
        # If all values are empty in preview than can be any field
        if values == {''}:
            return ['all']

        return ['id', 'text', 'boolean', 'char', 'datetime', 'selection', 'many2one', 'one2many', 'many2many', 'html']

    # def _match_headers(self, rows, fields, options):
    #     """ Attempts to match the imported model's fields to the
    #         titles of the parsed CSV file, if the file is supposed to have
    #         headers.
    #
    #         Will consume the first line of the ``rows`` iterator.
    #
    #         Returns the list of headers and a dict mapping cell indices
    #         to key paths in the ``fields`` tree. If headers were not
    #         requested, both collections are empty.
    #
    #         :param Iterator rows:
    #         :param dict fields:
    #         :param dict options:
    #         :rtype: (list(str), dict(int: list(str)))
    #     """
    #     if not options.get('headers'):
    #         return [], {}
    #
    #     headers = next(rows, None)
    #     if not headers:
    #         return [], {}
    #
    #     matches = {}
    #     mapping_records = self.env['base_import.mapping'].search_read([('res_model', '=', self.res_model)], ['column_name', 'field_name'])
    #     mapping_fields = {rec['column_name']: rec['field_name'] for rec in mapping_records}
    #     for index, header in enumerate(headers):
    #         match_field = []
    #         mapping_field_name = mapping_fields.get(header.lower())
    #         if mapping_field_name:
    #             match_field = mapping_field_name.split('/')
    #         if not match_field:
    #             match_field = [field['name'] for field in self._match_header(header, fields, options)]
    #         matches[index] = match_field or None
    #     return headers, matches

    # def _match_headers(self, rows, fields, options):
    #     if not options.get('headers'):
    #         return [], {}
    #
    #     headers = next(rows, None)
    #     if not headers:
    #         return [], {}
    #
    #     matches = {}
    #     mapping_records = []
    #     mapping_fields = {rec['column_name']: rec['field_name'] for rec in mapping_records}
    #     for index, header in enumerate(headers):
    #         match_field = []
    #         mapping_field_name = mapping_fields.get(header.lower())
    #         if mapping_field_name:
    #             match_field = mapping_field_name.split('/')
    #         if not match_field:
    #             match_field = [field['name'] for field in self._match_header(header.strip(), fields, options)]
    #         matches[index] = match_field or None
    #     return headers, matches

    #@api.multi
    # def _read_xls(self, options):
    #     """ Read file content, using xlrd lib """
    #     book = xlrd.open_workbook(file_contents=self.file or b'')
    #     sheets = book.sheet_names()
    #     sheet = sheets[0]
    #     return self._read_xls_book(book,sheet)

    # def _read_xls_book(self, book):
    #     sheet = book.sheet_by_index(0)
    #     # emulate Sheet.get_rows for pre-0.9.4
    #     for row in pycompat.imap(sheet.row, range(sheet.nrows)):
    #         values = []
    #         for cell in row:
    #             if cell.ctype is xlrd.XL_CELL_NUMBER:
    #                 is_float = cell.value % 1 != 0.0
    #                 values.append(
    #                     pycompat.text_type(cell.value)
    #                     if is_float
    #                     else pycompat.text_type(int(cell.value))
    #                 )
    #             elif cell.ctype is xlrd.XL_CELL_DATE:
    #                 is_datetime = cell.value % 1 != 0.0
    #                 # emulate xldate_as_datetime for pre-0.9.3
    #                 dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
    #                 values.append(
    #                     dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #                     if is_datetime
    #                     else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
    #                 )
    #             elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
    #                 values.append(u'True' if cell.value else u'False')
    #             elif cell.ctype is xlrd.XL_CELL_ERROR:
    #                 raise ValueError(
    #                     _("Error cell found while reading XLS/XLSX file: %s") %
    #                     xlrd.error_text_from_code.get(
    #                         cell.value, "unknown error code %s" % cell.value)
    #                 )
    #             else:
    #                 values.append(cell.value)
    #         if any(x for x in values if x.strip()):
    #             yield values

    # def _read_xls_book(self, book, sheet_name):
    #     sheet = book.sheet_by_name(sheet_name)
    #     # emulate Sheet.get_rows for pre-0.9.4
    #     for rowx, row in enumerate(map(sheet.row, range(sheet.nrows))):
    #         values = []
    #         for colx, cell in enumerate(row, 1):
    #             if cell.ctype is xlrd.XL_CELL_NUMBER:
    #                 is_float = cell.value % 1 != 0.0
    #                 values.append(
    #                     str(cell.value)
    #                     if is_float
    #                     else str(int(cell.value))
    #                 )
    #             elif cell.ctype is xlrd.XL_CELL_DATE:
    #                 is_datetime = cell.value % 1 != 0.0
    #                 # emulate xldate_as_datetime for pre-0.9.3
    #                 dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
    #                 values.append(
    #                     dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #                     if is_datetime
    #                     else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
    #                 )
    #             elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
    #                 values.append(u'True' if cell.value else u'False')
    #             elif cell.ctype is xlrd.XL_CELL_ERROR:
    #                 raise ValueError(
    #                     _("Invalid cell value at row %(row)s, column %(col)s: %(cell_value)s") % {
    #                         'row': rowx,
    #                         'col': colx,
    #                         'cell_value': xlrd.error_text_from_code.get(cell.value, _("unknown error code %s", cell.value))
    #                     }
    #                 )
    #             else:
    #                 values.append(cell.value)
    #         break
    #     # if any(x for x in values if x.strip()):
    #     #     yield values
    #     return values
    #
    # # use the same method for xlsx and xls files
    # _read_xlsx = _read_xls

    # @api.model
    # def get_fields(self, model, import_type_ven='', depth=FIELDS_RECURSION_LIMIT):
    #     Model = self.env['sps.vendor_offer_automation.template']
    #     importable_fields = []
    #     # importable_fields = [{
    #     #     'id': 'id',
    #     #     'name': 'id',
    #     #     'string': _("External ID"),
    #     #     'required': False,
    #     #     'fields': [],
    #     #     'type': 'id',
    #     # }]
    #     # if not depth:
    #     #     return importable_fields
    #     model_fields = Model.fields_get()
    #     blacklist = models.MAGIC_COLUMNS + [Model.CONCURRENCY_CHECK_FIELD]
    #     hide_column_list = []
    #     if import_type_ven == few_field_import:
    #         hide_column_list = hide_column_list_method
    #     for name, field in model_fields.items():
    #         if name in blacklist:
    #             continue
    #         if name in hide_column_list:
    #             continue
    #         # an empty string means the field is deprecated, @deprecated must
    #         # be absent or False to mean not-deprecated
    #         if field.get('deprecated', False) is not False:
    #             continue
    #         # if field.get('readonly'):
    #         #     states = field.get('states')
    #         #     if not states:
    #         #         continue
    #         #     # states = {state: [(attr, value), (attr2, value2)], state2:...}
    #         #     if not any(attr == 'readonly' and value is False
    #         #                for attr, value in itertools.chain.from_iterable(states.values())):
    #         #         continue
    #         if not name.startswith('mf_'):
    #             continue
    #         field_value = {
    #             'id': name,
    #             'name': name,
    #             'string': field['string'],
    #             # Y U NO ALWAYS HAS REQUIRED
    #             'required': bool(field.get('required')),
    #             'fields': [],
    #             'type': field['type'],
    #         }
    #
    #         if field['type'] in ('many2many', 'many2one'):
    #             field_value['fields'] = [
    #                 dict(field_value, name='id', string=_("External ID"), type='id'),
    #                 dict(field_value, name='.id', string=_("Database ID"), type='id'),
    #             ]
    #         elif field['type'] == 'one2many' and depth:
    #             field_value['fields'] = self.get_fields(field['relation'], depth=depth - 1)
    #             if self.user_has_groups('base.group_no_one'):
    #                 field_value['fields'].append(
    #                     {'id': '.id', 'name': '.id', 'string': _("Database ID"), 'required': False, 'fields': [],
    #                      'type': 'id'})
    #
    #         importable_fields.append(field_value)
    #
    #     # TODO: cache on model?
    #     return importable_fields

    @api.model
    def get_fields(self, model, import_type_ven, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env['sps.vendor_offer_automation.template']
        importable_fields = []
        importable_fields = [{
            'id': 'id',
            'name': 'id',
            'string': _("External ID"),
            'required': False,
            'fields': [],
            'type': 'id',
        }]
        model_fields = Model.fields_get()
        blacklist = models.MAGIC_COLUMNS + [Model.CONCURRENCY_CHECK_FIELD]
        for name, field in model_fields.items():
            if name in blacklist:
                continue
            if import_type_ven == 'new_appraisal' and name in hide_column_list_method_app_new:
                continue
            if field.get('deprecated', False) is not False:
                continue
            if field.get('readonly'):
                states = field.get('states')
                if not states:
                    continue
                if not any(attr == 'readonly' and value is False
                           for attr, value in itertools.chain.from_iterable(states.values())):
                    continue
            if not name.startswith('mf_'):
                continue
            field_value = {
                # 'id': name[3:],
                # 'name': name[3:],
                'id': name,
                'name': name,
                'string': field['string'],
                'required': bool(field.get('required')),
                'fields': [],
                'type': field['type'],
            }

            if field['type'] in ('many2many', 'many2one'):
                field_value['fields'] = [
                    dict(field_value, name='id', string=_("External ID"), type='id'),
                    dict(field_value, name='.id', string=_("Database ID"), type='id'),
                ]
            elif field['type'] == 'one2many' and depth:
                field_value['fields'] = self.get_fields(field['relation'], depth=depth - 1)
                if self.user_has_groups('base.group_no_one'):
                    field_value['fields'].append(
                        {'id': '.id', 'name': '.id', 'string': _("Database ID"), 'required': False, 'fields': [],
                         'type': 'id'})

            importable_fields.append(field_value)

        # TODO: cache on model?
        return importable_fields

    #@api.multi
    # def _parse_import_data(self,parent_model, data, import_fields, options):
    #     """ Lauch first call to _parse_import_data_recursive with an
    #     empty prefix. _parse_import_data_recursive will be run
    #     recursively for each relational field.
    #     """
    #     return self._parse_import_data_recursive(parent_model, '', data, import_fields, options)

    #@api.multi
    # def _parse_import_data_recursive(self, model, prefix, data, import_fields, options):
    #     # Get fields of type date/datetime
    #     all_fields = self.env[model].fields_get()
    #     for name, field in all_fields.items():
    #         name = prefix + name
    #         if field['type'] in ('date', 'datetime') and name in import_fields:
    #             index = import_fields.index(name)
    #             self._parse_date_from_data(data, index, name, field['type'], options)
    #         # Check if the field is in import_field and is a relational (followed by /)
    #         # Also verify that the field name exactly match the import_field at the correct level.
    #         elif any(name + '/' in import_field and name == import_field.split('/')[prefix.count('/')] for import_field
    #                  in import_fields):
    #             # Recursive call with the relational as new model and add the field name to the prefix
    #             self._parse_import_data_recursive(field['relation'], name + '/', data, import_fields, options)
    #         elif field['type'] in ('float', 'monetary') and name in import_fields:
    #             # Parse float, sometimes float values from file have currency symbol or () to denote a negative value
    #             # We should be able to manage both case
    #             index = import_fields.index(name)
    #             self._parse_float_from_data(data, index, name, options)
    #         elif field['type'] == 'binary' and field.get('attachment') and any(
    #                 f in name for f in IMAGE_FIELDS) and name in import_fields:
    #             index = import_fields.index(name)
    #
    #             with requests.Session() as session:
    #                 session.stream = True
    #
    #                 for num, line in enumerate(data):
    #                     if re.match(config.get("import_image_regex", DEFAULT_IMAGE_REGEX), line[index]):
    #                         if not self.env.user._can_import_remote_urls():
    #                             raise AccessError(_(
    #                                 "You can not import images via URL, check with your administrator or support for the reason."))
    #
    #                         line[index] = self._import_image_by_url(line[index], session, name, num)
    #
    #     return data
    # @staticmethod
    # def read_imported_file(self, vendor_offer_automation_template, partner_id, offer_id):
    #     book = xlrd.open_workbook(file_contents=self.file)
    #     try:
    #         pricing_index = book.sheet_names().index('PPVendorPricing')
    #     except:
    #         pricing_index = 0
    #     excel_columns = VendorOfferImportTransientModel._read_xls_book_custom(book, pricing_index, read_data=False)
    #     if len(excel_columns) == 1:
    #         excel_columns = excel_columns[0]
    #         model_fields = self.env['sps.vendor_offer_automation.template'].fields_get()
    #         mapping_fields = dict()
    #         for name, field in model_fields.items():
    #             if name.startswith('mf_'):
    #                 value = getattr(vendor_offer_automation_template, name, False)
    #                 if value:
    #                     mapping_fields.update({name: value})
    #     sku_index = None
    #     expiration_date_index = -1
    #     if 'mf_customer_sku' in mapping_fields:
    #         sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
    #     if 'mf_expiration_date' in mapping_fields:
    #         expiration_date_index = excel_columns.index(mapping_fields['mf_expiration_date'])
    #
    #     if not sku_index is None:
    #         todays_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #         # product_skus = []
    #         excel_data_rows = VendorOfferImportTransientModel._read_xls_book_custom(book, pricing_index, read_data=True,
    #                                                                  expiration_date_index=expiration_date_index)
    #         order_list_list = []
    #         for excel_data_row in excel_data_rows:
    #             sku_code = excel_data_row[sku_index]
    #             product_expiration_date = excel_data_row[expiration_date_index]
    #             product_sku = sku_code
    #             if partner_id.sku_preconfig and product_sku.startswith(
    #                     partner_id.sku_preconfig):
    #                 product_sku = product_sku[len(partner_id.sku_preconfig):]
    #             if partner_id.sku_postconfig and product_sku.endswith(
    #                     partner_id.sku_postconfig):
    #                 product_sku = product_sku[:-len(partner_id.sku_postconfig)]
    #             # un_matched_rows = 0
    #             # if not sku_code in product_skus:
    #             product_template = self.env['product.template'].search(
    #                 ['|', ('sku_code', '=', product_sku), ('manufacturer_pref', '=', sku_code)])
    #             if product_template:
    #                 products = self.env['product.product'].search(
    #                     [('product_tmpl_id', '=', product_template.id)])
    #                 product_unit_price = product_template.list_price
    #                 if len(products) > 0:
    #                     order_line_obj = dict(name=product_template.name, product_qty=1,
    #                                           date_planned=todays_date, state='ven_draft',
    #                                           product_uom=1, product_tier=product_template.tier.id,
    #                                           order_id=offer_id.id,
    #                                           product_id=products[0].id,
    #                                           # list_price=product_unit_price,
    #                                           qty_in_stock=products[0].qty_available,
    #                                           expiration_date=product_expiration_date)
    #                     order_line_obj.update(offer_id.get_product_sales_count(products[0].id))
    #                     multiplier_id = offer_id.get_order_line_multiplier(
    #                         order_line_obj, product_template.premium)
    #                     order_line_obj.update({'multiplier': multiplier_id})
    #                     multiplier_list = self.env['multiplier.multiplier'].search(
    #                         [('id', '=', multiplier_id)])
    #                     possible_competition_list = self.env['competition.competition'].search(
    #                         [('id', '=', offer_id.possible_competition.id)])
    #                     order_line_obj.update({'margin': multiplier_list.margin})
    #                     product_unit_price_wtih_multiplier = math.ceil(
    #                         round(float(product_unit_price) * (float(multiplier_list.retail) / 100), 2))
    #                     order_line_obj.update({
    #                         'price_unit': product_unit_price_wtih_multiplier,
    #                         'product_retail': product_unit_price_wtih_multiplier,
    #                         'product_unit_price': product_unit_price_wtih_multiplier})
    #                     product_offer_price_comp = math.ceil(
    #                         round(float(product_unit_price_wtih_multiplier) * (
    #                                 float(multiplier_list.margin) / 100 + float(
    #                             possible_competition_list.margin) / 100), 2))
    #                     order_line_obj.update(
    #                         {'product_offer_price': product_offer_price_comp,
    #                          # 'offer_price': product_offer_price_comp
    #                          })
    #                     order_list_list.append(order_line_obj)
    #                 # product_skus.append(sku_code)
    #         if len(order_list_list) > 0:
    #             for order_line_object in order_list_list:
    #                 order_line_model = self.env['purchase.order.line'].with_context(order_line_object)
    #                 order_line_model.create(order_line_object)

    # @staticmethod
    # def _read_xls_book_custom(book, pricing_index, read_data=False, expiration_date_index=-1):
    #     sheet = book.sheet_by_index(pricing_index)
    #     data = []
    #     row_index = 0
    #     for row in pycompat.imap(sheet.row, range(sheet.nrows)):
    #         if read_data is True and row_index == 0:
    #             row_index = row_index + 1
    #             continue
    #         values = []
    #         cell_index = 0
    #         for cell in row:
    #             if expiration_date_index == cell_index and not cell.value is None and str(cell.value) != '':
    #                 is_datetime = cell.value % 1 != 0.0
    #                 # emulate xldate_as_datetime for pre-0.9.3
    #                 dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
    #                 values.append(
    #                     dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #                     if is_datetime
    #                     else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
    #                 )
    #             else:
    #                 if cell.ctype is xlrd.XL_CELL_NUMBER:
    #                     is_float = cell.value % 1 != 0.0
    #                     values.append(
    #                         pycompat.text_type(cell.value)
    #                         if is_float
    #                         else pycompat.text_type(int(cell.value))
    #                     )
    #                 else:
    #                     values.append(cell.value)
    #             cell_index = cell_index + 1
    #         data.append(values)
    #         if not read_data:
    #             break
    #         row_index = row_index + 1
    #     return data

    # #@api.multi
    # def get_product_sales_count(self, product_id):
    #     product_sales_count = product_sales_count_month = product_sales_count_90 = product_sales_count_yrs = None
    #     try:
    #         groupby_dict_month = groupby_dict_90 = groupby_dict_yr = {}
    #
    #         total = total_m = total_90 = total_yr = 0
    #
    #         sale_orders = self.env['sale.order'].search(
    #             [('product_id', '=', product_id), ('state', '=', 'sale')])
    #
    #         filtered_by_date = list(
    #             filter(lambda x: not x.confirmation_date is None, sale_orders))
    #
    #         groupby_dict_month['data'] = filtered_by_date
    #         for sale_order_list in groupby_dict_month['data']:
    #             for sale_order in sale_order_list.order_line:
    #                 if sale_order.product_id.id == product_id:
    #                     total = total + sale_order.product_uom_qty
    #
    #         product_sales_count = total
    #
    #         filtered_by_date = list(
    #             filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
    #                     fields.date.today() - datetime.timedelta(days=30)), sale_orders))
    #         groupby_dict_month['data'] = filtered_by_date
    #         for sale_order_list in groupby_dict_month['data']:
    #             for sale_order in sale_order_list.order_line:
    #                 if sale_order.product_id.id == product_id:
    #                     total_m = total_m + sale_order.product_uom_qty
    #
    #         product_sales_count_month = total_m
    #
    #         filtered_by_90 = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
    #                 fields.date.today() - datetime.timedelta(days=90)), sale_orders))
    #         groupby_dict_90['data'] = filtered_by_90
    #
    #         for sale_order_list_90 in groupby_dict_90['data']:
    #             for sale_order in sale_order_list_90.order_line:
    #                 if sale_order.product_id.id == product_id:
    #                     total_90 = total_90 + sale_order.product_uom_qty
    #
    #         product_sales_count_90 = total_90
    #
    #         filtered_by_yr = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
    #                 fields.date.today() - datetime.timedelta(days=365)), sale_orders))
    #         groupby_dict_yr['data'] = filtered_by_yr
    #         for sale_order_list_yr in groupby_dict_yr['data']:
    #             for sale_order in sale_order_list_yr.order_line:
    #                 if sale_order.product_id.id == product_id:
    #                     total_yr = total_yr + sale_order.product_uom_qty
    #
    #         product_sales_count_yrs = total_yr
    #
    #         # product_sales_count = product_sales_count_month + product_sales_count_90 + product_sales_count_yrs
    #     except Exception as ex:
    #         _logger.error("Error", ex)
    #     return dict(product_sales_count=product_sales_count, product_sales_count_month=product_sales_count_month,
    #                 product_sales_count_90=product_sales_count_90, product_sales_count_yrs=product_sales_count_yrs)
