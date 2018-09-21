# -*- coding: utf-8 -*-
import json
import operator
import datetime

import xlwt
import re
import io

from odoo import fields,http
from odoo.exceptions import UserError
from odoo.http import request, serialize_exception, content_disposition
from odoo.tools import pycompat


class ExcelExport(http.Controller):
    # Excel needs raw data to correctly handle numbers and date values
    raw_data = True

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self, base):
        return base + '.xls'

    def from_data(self, fields, rows):
        if len(rows) > 65535:
            return

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        for i, fieldname in enumerate(fields):
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 8000  # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style

                if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
                    # because xls uses raw export, we can get a bytes object
                    # here. xlwt does not support bytes values in Python 3 ->
                    # assume this is base64 and decode to a string, if this
                    # fails note that you can't export
                    try:
                        cell_value = pycompat.to_text(cell_value)
                    except UnicodeDecodeError:
                        return

                if isinstance(cell_value, pycompat.string_types):
                    cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data


class WebsiteCstm(ExcelExport, http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('website_cstm.home_page')

    # @http.route('/contactus', type='http', auth="public", website=True)
    # def contact(self):
    #     return http.request.render('website_cstm.contact_page')

    @http.route('/about', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('website_cstm.about_page')

    @http.route('/faqs', type='http', auth="public", website=True)
    def faqs(self):
        return http.request.render('website_cstm.faqs_page')

    @http.route('/quality_assurance', type='http', auth="public", website=True)
    def quality_assurance_page(self):
        return http.request.render('website_cstm.qualityassurance_page')

    @http.route('/search', type='http', auth="public", website=True)
    def search(self):
        return http.request.render('website_cstm.search_page')

    @http.route('/product_types', type='http', auth="public", website=True)
    def product_types_page(self):
        values = {"categories": request.env['product.public.category'].search([('parent_id', '=', False)])}
        return http.request.render('website_cstm.product_types_page', values)

    @http.route('/notifyme', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def notifyme(self, product_id, email):
        StockNotifcation = request.env['website_cstm.product_instock_notify'].sudo()
        isSubcribed = StockNotifcation.search([
            ('product_tmpl_id', '=', int(product_id)),
            ('email', '=', email),
            ('status', '=', 'pending'),
        ], limit=1)
        if not isSubcribed:
            StockNotifcation.create({'status': 'pending', 'email': email, 'product_tmpl_id': product_id})
            return True
        else:
            return False

    @http.route('/downloadCatalog', type='http', auth="public", website=True)
    def downloadCatalog(self):
        data = '{"model":"product.template","fields":[],"ids":false,"domain":[["type","in",["consu","product"]],["type","in",["consu","product"]]],"context":{"lang":"en_US","tz":"Europe/Brussels","uid":1,"search_default_consumable":1,"default_type":"product","params":{"action":515}},"import_compat":false}'
        token = '1536750697732';
        return self.export(data, token)

    def formatDate(self,value):
        if not value:
            return None
        date = fields.Datetime.from_string(value)
        return str(date.month) + "/" + str(date.day) + "/" + str(date.year)

    def export(self, data, token):
        params = json.loads(data)
        params['fields'] = [
            {"name": "product_brand_id/display_name", "label": "OEM"},
            {"name": "sku_code", "label": "Catalog Number"},

            {"name": "name", "label": "Product Description"},
            {"name": "qty_available", "label": "Quantity "},

            {"name": "list_price", "label": "SPS Price Per Unit"},
            {"name": "standard_price", "label": "SPS SALES PRICE"},
            {"name": "product_variant_id/.id", "label": "Min Expiration Date"}
        ]

        model, fieldsa, ids, import_compat = operator.itemgetter('model', 'fields', 'ids',
                                                                         'import_compat')(params)

        Model = request.env[model].with_context(import_compat=import_compat, **params.get('context', {}))
        records = Model.browse(ids) or Model.search([('website_published', '=', True)],offset=0, limit=False, order=False)

        if not Model._is_an_ordinary_table():
            fieldsa = [field for field in fieldsa if field['name'] != 'id']

        field_names = [f['name'] for f in fieldsa]
        import_data = records.export_data(field_names, self.raw_data).get('datas', [])

        for val in import_data:
            request.env.cr.execute(
                "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = %s",
                (val[6],))
            if not val[0]:
                val[0] = ""
            query_result = request.env.cr.dictfetchone()
            val[6] = self.formatDate(query_result['min'])
            val.append(self.formatDate(query_result['max']))

        columns_headers = [val['label'].strip() for val in fieldsa]
        columns_headers.append("Max Expiration Date")

        return request.make_response(self.from_data(columns_headers, import_data),
                                     headers=[('Content-Disposition',
                                               content_disposition(self.filename("SPS_product_listing"))),
                                              ('Content-Type', self.content_type)],
                                     cookies={'fileToken': token})
