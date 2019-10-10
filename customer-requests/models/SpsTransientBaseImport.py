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
ATTACHMENT_DIR = "/home/odoo/Documents/templates/customer/"


class SpsTransientBaseImport(models.TransientModel):
    _inherit = 'base_import.import'
    _name = "sps.template.transient"
    # customer_id = fields.Integer('Customer')
    columns_from_template = fields.Char(string='Template Columns')

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Vendor Offer'),
            'template': '/vendor_offer_automation/static/xls/vendor_import.xlsx'
        }]

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

        rows_to_import = self._read_file(options)
        if options.get('headers'):
            rows_to_import = itertools.islice(rows_to_import, 0, None)
        data = [list(row) for row in pycompat.imap(mapper, rows_to_import) if any(row)]
        cols = data[0:1]

        cell_values = data[1:]
        return cell_values, import_fields, cols

    @api.multi
    def do(self, fields, columns,options, parent_model, customer_id, template_type, upload_document, dryrun=False):
        self.ensure_one()
        import_result = {'messages': []}
        try:
            data, import_fields, col = self._convert_import_data(fields, options)

            if 'mf_customer_sku' not in import_fields:
                raise ValueError(_("You must configure Customer Sku field to import"))
            if template_type == 'Inventory' and 'mf_quantity' not in import_fields:
                raise ValueError(_("You must configure Stock field to import"))

            if template_type == 'Requirement' and 'mf_required_quantity' not in import_fields:

                raise ValueError(_("You must configure Required Quantity field to import"))

            # if 'uom' not in import_fields:
            #     raise ValueError(_("You must configure UOM field to import"))

            self._cr.execute('SAVEPOINT import')
            if len(col) == 1:
                resource_model = self.env[parent_model]
                columns = col[0]
                dict_list = [{ import_field: columns[idx]} for idx, import_field in enumerate(import_fields)]
                resource_model_dict = dict(template_file=self.file, file_name=self.file_name,
                                           customer_id=customer_id)
                for dictionary in dict_list:
                    resource_model_dict.update(dictionary)
                resource_model_dict.update(dict(template_type=template_type, template_status='Active'))
                template_resources = resource_model.search([('customer_id', '=', customer_id)])
                for template_resource in template_resources:
                    template_resource.write(dict(template_status='InActive'))
                name_create_enabled_fields = options.pop('name_create_enabled_fields', {})
                template = resource_model.create(resource_model_dict).with_context(import_file=True,
                                                               name_create_enabled_fields=name_create_enabled_fields)
                # import_result = template.load(import_fields, data)
                import_result['ids'] = [template.id]

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
                            self.env['sps.document.process'].sudo().process_document(users_model,myfile_path,template_type,self.file_name, '', 'Manual')

                        else:
                            self._cr.execute('RELEASE SAVEPOINT import')

                except psycopg2.InternalError:
                    pass
        except ValueError as error:
            _logger.info('Error %r', str(error))
            return {
                'messages': [{
                    'type': 'error',
                    'message': pycompat.text_type(error),
                    'record': False,
                }]
            }
        return import_result

    @api.multi
    def parse_preview(self, options, count=10):
        self.ensure_one()
        fields = self.get_fields(self.res_model)
        try:
            rows = self._read_file(options)
            headers, matches = self._match_headers(rows, fields, options)
            self.columns_from_template = ".".join(headers)
            preview = list(itertools.islice(rows, count))
            assert preview, "CSV file seems to have no content"
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
    def get_fields(self, model, depth=FIELDS_RECURSION_LIMIT):
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