# -*- coding: utf-8 -*-

import itertools
import logging
import operator
import psycopg2
from .VendorOfferAutomationTemplate import *

IMAGE_FIELDS = ["icon", "image", "logo", "picture"]
DEFAULT_IMAGE_REGEX = r"(?:http|https)://.*(?:png|jpe?g|tiff?|gif|bmp)"

from odoo.tools.translate import _
from odoo.addons.base_import.models.base_import import ImportValidationError

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
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Vendor Offer'),
            'template': '/vendor_offer_automation/static/xls/vendor_import.xlsx'
        }]
    @api.model
    def _convert_import_data(self, fields, options, import_type_ven):
        """ Extracts the input BaseModel and fields list (with
            ``False``-y placeholders for fields to *not* import) into a
            format Model.import_data can use: a fields list without holes
            and the precisely matching data matrix

            :param list(str|bool): fields
            :returns: (data, fields)
            :rtype: (list(list(str)), list(str))
            :raises ValueError: in case the import data could not be converted
        """
        # Get indices for non-empty fields
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ImportValidationError(_("You must configure at least one field to import"))
        # If only one index, itemgetter will return an atom rather
        # than a 1-tuple
        if len(indices) == 1:
            mapper = lambda row: [row[indices[0]]]
        else:
            mapper = operator.itemgetter(*indices)
        # Get only list of actually imported fields
        import_fields = [f for f in fields if f]

        # BITS custom code starts .........................
        if 'mf_customer_sku' not in import_fields:
            raise ValueError(_("You must configure Customer SKU field to import"))

        if import_type_ven in (all_field_import, new_appraisal):
            if 'mf_quantity' not in import_fields:
                raise ValueError(_("You must configure 'Quantity' field to import"))

        if import_type_ven == all_field_import:
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


        _file_length, rows_to_import = self._read_file(options)
        if len(rows_to_import[0]) != len(fields):
            raise ImportValidationError(
                _("Error while importing records: all rows should be of the same size, but the title row has %d entries while the first row has %d. You may need to change the separator character.", len(fields), len(rows_to_import[0]))
            )

        if not options.get('has_headers'):
            raise ImportValidationError(
                _("Error while importing records: File Header Must be present in the document."))
            # rows_to_import = rows_to_import[1:]

        data = [
            list(row) for row in map(mapper, rows_to_import)
            # don't try inserting completely empty rows (e.g. from
            # filtering out o2m fields)
            if any(row)
        ]
        cols = data[:1]
        rows_data = data[1:]
        # slicing needs to happen after filtering out empty rows as the
        # data offsets from load are post-filtering
        return rows_data[options.get('skip'):], import_fields, cols

    # @api.model
    # def get_fields_tree(self, model, depth=FIELDS_RECURSION_LIMIT):
    #     """
    #     :param str model: name of the model to get fields form
    #     :param int depth: depth of recursion into o2m fields
    #     """
    #     Model = self.env[model]
    #     importable_fields = [{
    #         'id': 'id',
    #         'name': 'id',
    #         'string': _("External ID"),
    #         'required': False,
    #         'fields': [],
    #         'type': 'id',
    #     }]
    #     if not depth:
    #         return importable_fields
    #
    #     model_fields = Model.fields_get()
    #     blacklist = models.MAGIC_COLUMNS + [Model.CONCURRENCY_CHECK_FIELD]
    #     for name, field in model_fields.items():
    #         if name in blacklist:
    #             continue
    #         if import_type_ven == 'new_appraisal' and name in hide_column_list_method_app_new:
    #             continue
    #
    #         # an empty string means the field is deprecated, @deprecated must
    #         # be absent or False to mean not-deprecated
    #         if field.get('deprecated', False) is not False:
    #             continue
    #         if field.get('readonly'):
    #             states = field.get('states')
    #             if not states:
    #                 continue
    #             # states = {state: [(attr, value), (attr2, value2)], state2:...}
    #             if not any(attr == 'readonly' and value is False
    #                        for attr, value in itertools.chain.from_iterable(states.values())):
    #                 continue
    #         if not name.startswith('mf_'):
    #             continue
    #
    #         field_value = {
    #             'id': name,
    #             'name': name,
    #             'string': field['string'],
    #             # Y U NO ALWAYS HAS REQUIRED
    #             'required': bool(field.get('required')),
    #             'fields': [],
    #             'type': field['type'],
    #             'model_name': model
    #         }
    #
    #         if field['type'] in ('many2many', 'many2one'):
    #             field_value['fields'] = [
    #                 dict(field_value, name='id', string=_("External ID"), type='id'),
    #                 dict(field_value, name='.id', string=_("Database ID"), type='id'),
    #             ]
    #             field_value['comodel_name'] = field['relation']
    #         elif field['type'] == 'one2many':
    #             field_value['fields'] = self.get_fields_tree(field['relation'], depth=depth - 1)
    #             if self.user_has_groups('base.group_no_one'):
    #                 field_value['fields'].append(
    #                     {'id': '.id', 'name': '.id', 'string': _("Database ID"), 'required': False, 'fields': [],
    #                      'type': 'id'})
    #             field_value['comodel_name'] = field['relation']
    #
    #         importable_fields.append(field_value)
    #
    #     # TODO: cache on model?
    #     return importable_fields


    # def parse_preview(self, options, count=10):
    #     """ This method is coppied from odoo base import module and just override to get desired results        """
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
    #         elif options.get('has_headers'):
    #             matches = self._get_mapping_suggestions(headers, header_types, fields_tree)
    #             # remove header_name for matches keys as tuples are no supported in json.
    #             # and remove distance from suggestion (keep only the field path) as not used at client side.
    #             matches = {
    #                 header_key[0]: suggestion['field_path']
    #                 for header_key, suggestion in matches.items()
    #                 if suggestion
    #             }
    #
    #         # compute if we should activate advanced mode or not:
    #         # if was already activated of if file contains "relational fields".
    #         if options.get('keep_matches'):
    #             advanced_mode = options.get('advanced')
    #         else:
    #             # Check is label contain relational field
    #             has_relational_header = any(len(models.fix_import_export_id_paths(col)) > 1 for col in headers)
    #             # Check is matches fields have relational field
    #             has_relational_match = any(len(match) > 1 for field, match in matches.items() if match)
    #             advanced_mode = has_relational_header or has_relational_match
    #
    #         # Take first non null values for each column to show preview to users.
    #         # Initially first non null value is displayed to the user.
    #         # On hover preview consists in 5 values.
    #         column_example = []
    #         for column_index, _unused in enumerate(preview[0]):
    #             vals = []
    #             for record in preview:
    #                 if record[column_index]:
    #                     vals.append("%s%s" % (record[column_index][:50], "..." if len(record[column_index]) > 50 else ""))
    #                 if len(vals) == 5:
    #                     break
    #             column_example.append(
    #                 vals or
    #                 [""]  # blank value if no example have been found at all for the current column
    #             )
    #
    #         # Batch management
    #         batch = False
    #         batch_cutoff = options.get('limit')
    #         if batch_cutoff:
    #             if count > batch_cutoff:
    #                 batch = len(preview) > batch_cutoff
    #             else:
    #                 batch = bool(next(
    #                     itertools.islice(rows, batch_cutoff - count, None),
    #                     None
    #                 ))
    #
    #         return {
    #             'fields': fields_tree,
    #             'matches': matches or False,
    #             'headers': headers or False,
    #             'header_types': list(header_types.values()) or False,
    #             'preview': column_example,
    #             'options': options,
    #             'advanced_mode': advanced_mode,
    #             'debug': self.user_has_groups('base.group_no_one'),
    #             'batch': batch,
    #             'file_length': file_length
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

    def cus_execute_import(self, fields, columns, options, parent_model, customer_id, template_type, upload_document, offer_id, import_type_ven, dryrun=False):
        """
        Actual execution of the import
        """
        self.ensure_one()
        self._cr.execute('SAVEPOINT import')
        try:
            input_file_data, import_fields, cols = self._convert_import_data(fields, options, import_type_ven)
            columns = cols[0]
            # Parse date and float field
            input_file_data = self._parse_import_data(input_file_data, import_fields, options)
        except ImportValidationError as error:
            return {'messages': [error.__dict__]}

        _logger.info('importing %d rows...', len(input_file_data))

        import_fields, merged_data = self._handle_multi_mapping(import_fields, input_file_data)

        if options.get('fallback_values'):
            merged_data = self._handle_fallback_values(import_fields, merged_data, options['fallback_values'])

        name_create_enabled_fields = options.pop('name_create_enabled_fields', {})
        import_limit = options.pop('limit', None)
        model = self.env[self.res_model].with_context(
            import_file=True,
            name_create_enabled_fields=name_create_enabled_fields,
            import_set_empty_fields=options.get('import_set_empty_fields', []),
            import_skip_records=options.get('import_skip_records', []),
            _import_limit=import_limit)
        import_result = model.load(import_fields, merged_data)
        import_result['messages'] = []
        _logger.info('done')

        # If transaction aborted, RELEASE SAVEPOINT is going to raise
        # an InternalError (ROLLBACK should work, maybe). Ignore that.
        # TODO: to handle multiple errors, create savepoint around
        #       write and release it in case of write error (after
        #       adding error to errors array) => can keep on trying to
        #       import stuff, and rollback at the end if there is any
        #       error in the results.
        try:
            if dryrun:
                self._cr.execute('ROLLBACK TO SAVEPOINT import')
                # cancel all changes done to the registry/ormcache
                self.pool.clear_caches()
                self.pool.reset_changes()
            else:
                self._cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        # Insert/Update mapping columns when import complete successfully
        if import_result['ids'] and options.get('has_headers'):
            BaseImportMapping = self.env['base_import.mapping']
            for index, column_name in enumerate(columns):
                if column_name:
                    # Update to latest selected field
                    mapping_domain = [('res_model', '=', self.res_model), ('column_name', '=', column_name)]
                    column_mapping = BaseImportMapping.search(mapping_domain, limit=1)
                    if column_mapping:
                        if column_mapping.field_name != fields[index]:
                            column_mapping.field_name = fields[index]
                    else:
                        BaseImportMapping.create({
                            'res_model': self.res_model,
                            'column_name': column_name,
                            'field_name': fields[index]
                        })
        if 'name' in import_fields:
            index_of_name = import_fields.index('name')
            skipped = options.get('skip', 0)
            # pad front as data doesn't contain anythig for skipped lines
            r = import_result['name'] = [''] * skipped
            # only add names for the window being imported
            r.extend(x[index_of_name] for x in input_file_data[:import_limit])
            # pad back (though that's probably not useful)
            r.extend([''] * (len(input_file_data) - (import_limit or 0)))
        else:
            import_result['name'] = []

        skip = options.get('skip', 0)
        # convert load's internal nextrow to the imported file's
        if import_result['nextrow']: # don't update if nextrow = 0 (= no nextrow)
            import_result['nextrow'] += skip

        resource_model = self.env[parent_model]
        # columns = col[0]
        dict_list = [{import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
        resource_model_dict = dict(template_status='Active', file_name=self.file_name,
                                   columns_from_template=self.columns_from_template,
                                   customer_id=customer_id)
        for dictionary in dict_list:
            resource_model_dict.update(dictionary)
        name_create_enabled_fields = options.pop('name_create_enabled_fields', {})

        template = resource_model.create(resource_model_dict).with_context(import_file=True, name_create_enabled_fields=name_create_enabled_fields)
        import_result = template.load(import_fields, input_file_data)

        vendor_offer = self.env['purchase.order'].search([('id', '=', offer_id)])

        if len(vendor_offer) == 1:
            vendor_offer.sudo().write({'template_id': template.id, 'document': self.file, 'import_type_ven': import_type_ven})

        return import_result
