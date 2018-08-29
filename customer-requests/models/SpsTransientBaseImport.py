# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import operator
import psycopg2
import itertools

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


class SpsTransientBaseImport(models.Model):
    _inherit = 'base_import.import'
    _name = "sps.template.transient"
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

        if 'customer_sku' not in import_fields:
            raise ValueError(_("You must configure Customer Sku field to import"))

        rows_to_import = self._read_file(options)
        if options.get('headers'):
            rows_to_import = itertools.islice(rows_to_import, 0, None)
        data = [list(row) for row in pycompat.imap(mapper, rows_to_import) if any(row)]
        cols = data[0:1]

        cell_values = data[1:]
        return cell_values, import_fields, cols

    @api.multi
    def do(self, fields, options, parent_model, customer_id, template_type, dryrun=False):
        self.ensure_one()
        import_result = {'messages': []}
        try:
            self._cr.execute('SAVEPOINT import')
            data, import_fields, col = self._convert_import_data(fields, options)
            if len(col) == 1:
                resource_model = self.env[parent_model]
                columns = col[0]
                dict_list = [{'mf_' + import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
                resource_model_dict = dict(template_file=self.file, file_name=self.file_name,
                                           customer_id=customer_id)
                for dictionary in dict_list:
                    resource_model_dict.update(dictionary)
                resource_model_dict.update(dict(template_type=template_type, template_status='Active'))
                template_resources = resource_model.search([('template_type', '=', template_type),
                                                            ('customer_id', '=', customer_id)])
                for template_resource in template_resources:
                    template_resource.write(dict(template_status='InActive'))
                resource_model.create(resource_model_dict)
                try:
                    if dryrun:
                        self._cr.execute('ROLLBACK TO SAVEPOINT import')
                    else:
                        self._cr.execute('RELEASE SAVEPOINT import')
                except psycopg2.InternalError:
                    pass
        except ValueError as error:
            return [{
                'type': 'error',
                'message': pycompat.text_type(error),
                'record': False,
            }]
        return import_result['messages']

    @api.multi
    def parse_preview(self, options, count=10):
        """ Generates a preview of the uploaded files, and performs
            fields-matching between the import's file data and the model's
            columns.

            If the headers are not requested (not options.headers),
            ``matches`` and ``headers`` are both ``False``.

            :param int count: number of preview lines to generate
            :param options: format-specific options.
                            CSV: {encoding, quoting, separator, headers}
            :type options: {str, str, str, bool}
            :returns: {fields, matches, headers, preview} | {error, preview}
            :rtype: {dict(str: dict(...)), dict(int, list(str)), list(str), list(list(str))} | {str, str}
        """
        self.ensure_one()
        fields = self.get_fields(self.res_model)
        try:
            rows = self._read_file(options)
            headers, matches = self._match_headers(rows, fields, options)
            # Match should have consumed the first row (iif headers), get
            # the ``count`` next rows for preview
            self.columns_from_template = ".".join(headers)
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
