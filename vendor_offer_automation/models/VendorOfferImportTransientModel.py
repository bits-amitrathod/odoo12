# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import operator
import psycopg2
import itertools
import math
import base64

from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

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

_logger = logging.getLogger(__name__)


class VendorOfferImportTransientModel(models.TransientModel):
    _inherit = 'base_import.import'
    _name = "sps.vendor.offer.template.transient"
    # customer_id = fields.Integer('Customer')
    columns_from_template = fields.Char(string='Template Columns')


    @api.model
    def _convert_import_data(self, fields, options):
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ValueError(_("You must configure at least one field to import"))
        if len(indices) == 1:
            mapper = lambda row: [row[indices[0]]]
        else:
            mapper = operator.itemgetter(*indices)
        import_fields = [f for f in fields if f]

        if 'mf_customer_sku' not in import_fields:
            raise ValueError(_("You must configure Customer Sku field to import"))

        rows_to_import = self._read_file(options)
        if options.get('headers'):
            rows_to_import = itertools.islice(rows_to_import, 0, None)
        data = [list(row) for row in pycompat.imap(mapper, rows_to_import) if any(row)]
        cols = data[0:1]

        cell_values = data[1:]
        return cell_values, import_fields, cols

    @api.multi
    def do(self, fields, options, parent_model, customer_id, offer_id, dryrun=False):
        self.ensure_one()
        import_result = {'messages': []}
        try:
            self._cr.execute('SAVEPOINT import')
            data, import_fields, col = self._convert_import_data(fields, options)
            if len(col) == 1:

                resource_model = self.env[parent_model]
                columns = col[0]
                dict_list = [{ import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
                resource_model_dict = dict(template_status='Active', file_name=self.file_name,
                                           columns_from_template=self.columns_from_template,
                                           customer_id=customer_id)
                for dictionary in dict_list:
                    resource_model_dict.update(dictionary)
                template = resource_model.create(resource_model_dict)

                vendor_offer = self.env['purchase.order'].search([('id', '=', offer_id)])

                if len(vendor_offer) == 1:
                    vendor_offer[0].write({'template_id': template.id, 'document': self.file})
                try:
                    if dryrun:
                        self._cr.execute('ROLLBACK TO SAVEPOINT import')
                    else:
                        self._cr.execute('RELEASE SAVEPOINT import')
                except psycopg2.InternalError:
                    pass
        except ValueError as error:
            _logger.info('Error %r', str(error))
            return [{
                'type': 'error',
                'message': pycompat.text_type(error),
                'record': False,
            }]
        return import_result['messages']

    @api.multi
    def parse_preview(self, options, count=10):
        self.ensure_one()
        fields = self.get_fields(self.res_model)
        try:
            rows = self._read_file(options)
            headers, matches = self._match_headers(rows, fields, options)
            # _logger.info('headers %r', headers)
            # Match should have consumed the first row (iif headers), get
            # the ``count`` next rows for preview
            self.columns_from_template = ",".join(sorted(headers))
            preview = list(itertools.islice(rows, count))
            assert preview, "CSV file seems to have no content"
            header_types = self._find_type_from_preview(options, preview)
            if options.get('keep_matches', False) and len(options.get('fields', [])):
                matches = {}
                for index, match in enumerate(options.get('fields')):
                    if match:
                        matches[index] = match.split('/')

            return {
                'fields': fields,
                'matches': matches or False,
                'headers': headers or False,
                'headers_type': header_types or False,
                'preview': preview,
                'options': options,
                'debug': self.user_has_groups('base.group_no_one'),
            }
        except Exception as error:
            # Due to lazy generators, UnicodeDecodeError (for
            # instance) may only be raised when serializing the
            # preview to a list in the return.
            _logger.debug("Error during parsing preview", exc_info=True)
            preview = None
            if self.file_type == 'text/csv':
                preview = self.file[:ERROR_PREVIEW_BYTES].decode('iso-8859-1')
            return {
                'error': str(error),
                # iso-8859-1 ensures decoding will always succeed,
                # even if it yields non-printable characters. This is
                # in case of UnicodeDecodeError (or csv.Error
                # compounded with UnicodeDecodeError)
                'preview': preview,
            }

    @api.multi
    def _read_xls(self, options):
        """ Read file content, using xlrd lib """
        book = xlrd.open_workbook(file_contents=self.file)
        return self._read_xls_book(book)

    def _read_xls_book(self, book):
        sheet = book.sheet_by_index(0)
        # emulate Sheet.get_rows for pre-0.9.4
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                values.append(pycompat.text_type(cell.value))
            if any(x for x in values if x.strip()):
                yield values

    # use the same method for xlsx and xls files
    _read_xlsx = _read_xls

    @api.model
    def get_fields(self, model, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env['sps.vendor_offer_automation.template']
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
            # an empty string means the field is deprecated, @deprecated must
            # be absent or False to mean not-deprecated
            if field.get('deprecated', False) is not False:
                continue
            if field.get('readonly'):
                states = field.get('states')
                if not states:
                    continue
                # states = {state: [(attr, value), (attr2, value2)], state2:...}
                if not any(attr == 'readonly' and value is False
                           for attr, value in itertools.chain.from_iterable(states.values())):
                    continue
            if not name.startswith('mf_'):
                continue
            field_value = {
                'id': name,
                'name': name,
                'string': field['string'],
                # Y U NO ALWAYS HAS REQUIRED
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

    # @staticmethod
    def read_imported_file(self, vendor_offer_automation_template, partner_id, offer_id):
        book = xlrd.open_workbook(file_contents=self.file)
        try:
            pricing_index = book.sheet_names().index('PPVendorPricing')
        except:
            pricing_index = 0
        excel_columns = VendorOfferImportTransientModel._read_xls_book_custom(book, pricing_index, read_data=False)
        if len(excel_columns) == 1:
            excel_columns = excel_columns[0]
            model_fields = self.env['sps.vendor_offer_automation.template'].fields_get()
            mapping_fields = dict()
            for name, field in model_fields.items():
                if name.startswith('mf_'):
                    value = getattr(vendor_offer_automation_template, name, False)
                    if value:
                        mapping_fields.update({name: value})
        sku_index = None
        expiration_date_index = -1
        if 'mf_customer_sku' in mapping_fields:
            sku_index = excel_columns.index(mapping_fields['mf_customer_sku'])
        if 'mf_expiration_date' in mapping_fields:
            expiration_date_index = excel_columns.index(mapping_fields['mf_expiration_date'])

        if not sku_index is None:
            todays_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            product_skus = []
            excel_data_rows = VendorOfferImportTransientModel._read_xls_book_custom(book, pricing_index, read_data=True,
                                                                     expiration_date_index=expiration_date_index)
            order_list_list = []
            for excel_data_row in excel_data_rows:
                sku_code = excel_data_row[sku_index]
                product_expiration_date = excel_data_row[expiration_date_index]
                product_sku = sku_code
                if partner_id.sku_preconfig and product_sku.startswith(
                        partner_id.sku_preconfig):
                    product_sku = product_sku[len(partner_id.sku_preconfig):]
                if partner_id.sku_postconfig and product_sku.endswith(
                        partner_id.sku_postconfig):
                    product_sku = product_sku[:-len(partner_id.sku_postconfig)]
                un_matched_rows = 0
                if not sku_code in product_skus:
                    product_template = self.env['product.template'].search(
                        ['|', ('sku_code', '=', product_sku), ('manufacturer_pref', '=', sku_code)])
                    if product_template:
                        products = self.env['product.product'].search(
                            [('product_tmpl_id', '=', product_template.id)])
                        product_unit_price = product_template.list_price
                        if len(products) > 0:
                            order_line_obj = dict(name=product_template.name, product_qty=1,
                                                  date_planned=todays_date, state='ven_draft',
                                                  product_uom=1, product_tier=product_template.tier.id,
                                                  order_id=offer_id.id,
                                                  product_id=products[0].id,
                                                  list_price=product_unit_price,
                                                  qty_in_stock=products[0].qty_available,
                                                  expiration_date=product_expiration_date)
                            order_line_obj.update(offer_id.get_product_sales_count(products[0].id))
                            multiplier_id = offer_id.get_order_line_multiplier(
                                order_line_obj, product_template.premium)
                            order_line_obj.update({'multiplier': multiplier_id})
                            multiplier_list = self.env['multiplier.multiplier'].search(
                                [('id', '=', multiplier_id)])
                            possible_competition_list = self.env['competition.competition'].search(
                                [('id', '=', offer_id.possible_competition.id)])
                            order_line_obj.update({'margin': multiplier_list.margin})
                            product_unit_price_wtih_multiplier = math.ceil(
                                round(float(product_unit_price) * (float(multiplier_list.retail) / 100), 2))
                            order_line_obj.update({
                                'price_unit': product_unit_price_wtih_multiplier,
                                'product_retail': product_unit_price_wtih_multiplier,
                                'product_unit_price': product_unit_price_wtih_multiplier})
                            product_offer_price_comp = math.ceil(
                                round(float(product_unit_price_wtih_multiplier) * (
                                        float(multiplier_list.margin) / 100 + float(
                                    possible_competition_list.margin) / 100), 2))
                            order_line_obj.update(
                                {'product_offer_price': product_offer_price_comp,
                                 'offer_price': product_offer_price_comp})
                            order_list_list.append(order_line_obj)
                    else:
                        un_matched_rows = un_matched_rows + 1
                    product_skus.append(sku_code)
            if len(order_list_list) > 0:
                for order_line_object in order_list_list:
                    order_line_model = self.env['purchase.order.line'].with_context(order_line_object)
                    order_line_model.create(order_line_object)

    @staticmethod
    def _read_xls_book_custom(book, pricing_index, read_data=False, expiration_date_index=-1):
        sheet = book.sheet_by_index(pricing_index)
        data = []
        row_index = 0
        for row in pycompat.imap(sheet.row, range(sheet.nrows)):
            if read_data is True and row_index == 0:
                row_index = row_index + 1
                continue
            values = []
            cell_index = 0
            for cell in row:
                if expiration_date_index == cell_index and not cell.value is None and str(cell.value) != '':
                    is_datetime = cell.value % 1 != 0.0
                    # emulate xldate_as_datetime for pre-0.9.3
                    dt = datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                else:
                    if cell.ctype is xlrd.XL_CELL_NUMBER:
                        is_float = cell.value % 1 != 0.0
                        values.append(
                            pycompat.text_type(cell.value)
                            if is_float
                            else pycompat.text_type(int(cell.value))
                        )
                    else:
                        values.append(cell.value)
                cell_index = cell_index + 1
            data.append(values)
            if not read_data:
                break
            row_index = row_index + 1
        return data

    @api.multi
    def get_product_sales_count(self, product_id):
        product_sales_count = product_sales_count_month = product_sales_count_90 = product_sales_count_yrs = None
        try:
            groupby_dict_month = groupby_dict_90 = groupby_dict_yr = {}

            total = total_m = total_90 = total_yr = 0

            sale_orders = self.env['sale.order'].search(
                [('product_id', '=', product_id), ('state', '=', 'sale')])

            filtered_by_date = list(
                filter(lambda x: not x.confirmation_date is None, sale_orders))

            groupby_dict_month['data'] = filtered_by_date
            for sale_order_list in groupby_dict_month['data']:
                for sale_order in sale_order_list.order_line:
                    if sale_order.product_id.id == product_id:
                        total = total + sale_order.product_uom_qty

            product_sales_count = total

            filtered_by_date = list(
                filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                        fields.date.today() - datetime.timedelta(days=30)), sale_orders))
            groupby_dict_month['data'] = filtered_by_date
            for sale_order_list in groupby_dict_month['data']:
                for sale_order in sale_order_list.order_line:
                    if sale_order.product_id.id == product_id:
                        total_m = total_m + sale_order.product_uom_qty

            product_sales_count_month = total_m

            filtered_by_90 = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                    fields.date.today() - datetime.timedelta(days=90)), sale_orders))
            groupby_dict_90['data'] = filtered_by_90

            for sale_order_list_90 in groupby_dict_90['data']:
                for sale_order in sale_order_list_90.order_line:
                    if sale_order.product_id.id == product_id:
                        total_90 = total_90 + sale_order.product_uom_qty

            product_sales_count_90 = total_90

            filtered_by_yr = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (
                    fields.date.today() - datetime.timedelta(days=365)), sale_orders))
            groupby_dict_yr['data'] = filtered_by_yr
            for sale_order_list_yr in groupby_dict_yr['data']:
                for sale_order in sale_order_list_yr.order_line:
                    if sale_order.product_id.id == product_id:
                        total_yr = total_yr + sale_order.product_uom_qty

            product_sales_count_yrs = total_yr

            # product_sales_count = product_sales_count_month + product_sales_count_90 + product_sales_count_yrs
        except Exception as ex:
            _logger.error("Error", ex)
        return dict(product_sales_count=product_sales_count, product_sales_count_month=product_sales_count_month,
                    product_sales_count_90=product_sales_count_90, product_sales_count_yrs=product_sales_count_yrs)
