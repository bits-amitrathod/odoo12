# -*- coding: utf-8 -*-

import logging
import operator
import psycopg2
import itertools
from odoo.addons.base_import.models.base_import import ImportValidationError

from odoo.tools.translate import _

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
ATTACHMENT_DIR = "/home/odoo/Documents/templates/customer/"


class SpsTransientBaseImport(models.TransientModel):
    _inherit = 'base_import.import'
    _name = "sps.template.transient"
    _description = "Sps Transient Base Import"

    # customer_id = fields.Integer('Customer')
    columns_from_template = fields.Char(string='Template Columns')

    # @api.model
    # def get_import_templates(self):
    #     return [{
    #         'label': _('Import Template for Vendor Offer'),
    #         'template': '/vendor_offer_automation/static/xls/vendor_import.xlsx'
    #     }]
    #
    # @api.model
    def _convert_import_data(self, fields, options):
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ValueError(_("You must configure at least one field to import"))
        if len(indices) == 1:
            mapper = lambda row: [row[indices[0]]]
        else:
            mapper = operator.itemgetter(*indices)
        import_fields = [f for f in fields if f]

        rows_to_import = self._read_file(options)
        if options.get('headers'):
            rows_to_import = itertools.islice(rows_to_import, 0, None)
        data = [list(row) for row in map(mapper, rows_to_import[1]) if any(row)]
        cols = data[0:1]

        cell_values = data[1:]
        return cell_values, import_fields, cols

    #  This Method Called from template_import
    def execute_import(self, fields, columns,options, parent_model, customer_id, template_type, upload_document, dryrun=False):
        self.ensure_one()
        import_result = {'messages': []}
        try:
            data, import_fields, col = self._convert_import_data(fields, options)

            # if 'mf_customer_sku' not in import_fields:
            #     raise ValueError(_("You must configure Customer Sku field to import"))
            # if template_type == 'Inventory' and 'mf_quantity' not in import_fields:
            #     raise ValueError(_("You must configure Stock field to import"))

            # if template_type == 'Requirement' and 'mf_required_quantity' not in import_fields:
            #
            #     raise ValueError(_("You must configure Required Quantity field to import"))

            # if 'mf_uom' not in import_fields:
            #     raise ValueError(_("You must configure UOM field to import"))

            self._cr.execute('SAVEPOINT import')
            if len(col) == 1:
                resource_model = self.env[parent_model]
                columns = col[0]
                dict_list = [{import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
                resource_model_dict = dict(template_file=self.file, file_name=self.file_name,
                                           customer_id=customer_id)
                for dictionary in dict_list:
                    resource_model_dict.update(dictionary)
                resource_model_dict.update(dict(template_type=template_type, template_status='Active'))
                template_resources = resource_model.search([('customer_id', '=', customer_id)])
                for template_resource in template_resources:
                    template_resource.write(dict(template_status='InActive'))
                name_create_enabled_fields = options.pop('name_create_enabled_fields', {})
                template = resource_model.with_context(import_file=True, name_create_enabled_fields=name_create_enabled_fields).create(resource_model_dict)
                # import_result = model.load(import_fields, data)
                import_result['ids'] = [template['id']]

                try:
                    if dryrun:
                        self._cr.execute('ROLLBACK TO SAVEPOINT import')
                        self.pool.reset_changes()
                    else:
                        if upload_document == 'True':
                            self._cr.execute('RELEASE SAVEPOINT import')
                            users_model = self.env['res.partner'].search([("id", "=", customer_id)])
                            directory_path = ATTACHMENT_DIR + str(customer_id) + "/" + template_type + "/"
                            myfile_path = directory_path + str(self.file_name)
                            self.env['sps.document.process'].sudo().process_document(users_model, myfile_path, template_type, self.file_name, '', 'Manual')
                        else:
                            self._cr.execute('RELEASE SAVEPOINT import')

                except psycopg2.InternalError:
                    print('Internal error')
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
        return import_result

    # def parse_preview(self, options, count=10):
    #     self.ensure_one()
    #     fields_tree = self.get_fields_tree(self.res_model)
    #     try:
    #         file_length, rows = self._read_file(options)
    #         if file_length <= 0:
    #             raise ImportValidationError(_("Import file has no content or is corrupt"))
    #
    #         preview = rows[:count]
    #
    #         # Get file headers
    #         if options.get('has_headers') and preview:
    #             # We need the header types before matching columns to fields
    #             headers = preview.pop(0)
    #             header_types = self._extract_headers_types(headers, preview, options)
    #         else:
    #             header_types, headers = {}, []
    #
    #         # Get matches: the ones already selected by the user or propose a new matching.
    #         matches = {}
    #         # If user checked to the advanced mode, we re-parse the file but we keep the mapping "as is".
    #         # No need to make another mapping proposal
    #         if options.get('keep_matches') and options.get('fields'):
    #             for index, match in enumerate(options.get('fields', [])):
    #                 if match:
    #                     matches[index] = match.split('/')
    #         # elif options.get('has_headers'):
    #         #     matches = self._get_mapping_suggestions(headers, header_types, fields_tree)
    #         #     # remove header_name for matches keys as tuples are no supported in json.
    #         #     # and remove distance from suggestion (keep only the field path) as not used at client side.
    #         #     matches = {
    #         #         header_key[0]: suggestion['field_path']
    #         #         for header_key, suggestion in matches.items()
    #         #         if suggestion
    #         #     }
    #
    #         # compute if we should activate advanced mode or not:
    #         # if was already activated of if file contains "relational fields".
    #         # if options.get('keep_matches'):
    #         #     advanced_mode = options.get('advanced')
    #         # else:
    #         #     # Check is label contain relational field
    #         #     has_relational_header = any(len(models.fix_import_export_id_paths(col)) > 1 for col in headers)
    #         #     # Check is matches fields have relational field
    #         #     has_relational_match = any(len(match) > 1 for field, match in matches.items() if match)
    #         #     advanced_mode = has_relational_header or has_relational_match
    #
    #         # Take first non null values for each column to show preview to users.
    #         # Initially first non null value is displayed to the user.
    #         # On hover preview consists in 5 values.
    #         # column_example = []
    #         # for column_index, _unused in enumerate(preview[0]):
    #         #     vals = []
    #         #     for record in preview:
    #         #         if record[column_index]:
    #         #             vals.append("%s%s" % (record[column_index][:50], "..." if len(record[column_index]) > 50 else ""))
    #         #         if len(vals) == 5:
    #         #             break
    #         #     column_example.append(
    #         #         vals or
    #         #         [""]  # blank value if no example have been found at all for the current column
    #         #     )
    #
    #         # Batch management
    #         # batch = False
    #         # batch_cutoff = options.get('limit')
    #         # if batch_cutoff:
    #         #     if count > batch_cutoff:
    #         #         batch = len(preview) > batch_cutoff
    #         #     else:
    #         #         batch = bool(next(
    #         #             itertools.islice(rows, batch_cutoff - count, None),
    #         #             None
    #         #         ))
    #
    #         return {
    #             'fields': fields_tree,
    #             'matches': matches or False,
    #             'headers': headers or False,
    #             'header_types': list(header_types.values()) or False,
    #             'preview': preview,
    #             'options': options,
    #             # 'advanced_mode': advanced_mode,
    #             'debug': self.user_has_groups('base.group_no_one'),
    #             # 'batch': batch,
    #             # 'file_length': file_length
    #         }
    #     except Exception as error:
    #         # Due to lazy generators, UnicodeDecodeError (for
    #         # instance) may only be raised when serializing the
    #         # preview to a list in the return.
    #         _logger.debug("Error during parsing preview", exc_info=True)
    #         preview = None
    #         if self.file_type == 'text/csv' and self.file:
    #             preview = self.file[:ERROR_PREVIEW_BYTES].decode('iso-8859-1')
    #         return {
    #             'error': str(error),
    #             # iso-8859-1 ensures decoding will always succeed,
    #             # even if it yields non-printable characters. This is
    #             # in case of UnicodeDecodeError (or csv.Error
    #             # compounded with UnicodeDecodeError)
    #             'preview': preview,
    #         }

    def get_fields_tree(self, model, depth=FIELDS_RECURSION_LIMIT):
        Model = self.env['sps.customer.template']
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
                field_value['comodel_name'] = field['relation']
            elif field['type'] == 'one2many':
                field_value['fields'] = self.get_fields_tree(field['relation'], depth=depth-1)
            if self.user_has_groups('base.group_no_one'):
                field_value['fields'].append(
                    {'id': '.id', 'name': '.id', 'string': _("Database ID"), 'required': False, 'fields': [],
                     'type': 'id'})
            importable_fields.append(field_value)

        # TODO: cache on model?
        return importable_fields