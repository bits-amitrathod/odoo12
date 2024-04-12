
from odoo import api, models
import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools import pdf
from odoo.tools import pycompat
from werkzeug.urls import url_encode
from odoo import http
import io
import re
from odoo.addons.web.controllers.main import content_disposition
#from reports.report_custom_product_catalog.models.catalog import InventoryCustomProductPopUp

try:
    import xlwt


    # add some sanitizations to respect the excel sheet name restrictions
    # as the sheet name is often translatable, can not control the input
    class PatchedWorkbook(xlwt.Workbook):
        def add_sheet(self, name, cell_overwrite_ok=False):
            # invalid Excel character: []:*?/\
            name = re.sub(r'[\[\]:*?/\\]', '', name)

            # maximum size is 31 characters
            name = name[:31]
            return super(PatchedWorkbook, self).add_sheet(name, cell_overwrite_ok=cell_overwrite_ok)


    xlwt.Workbook = PatchedWorkbook

except ImportError:
    xlwt = None



class ReportCustomProductCatalog(models.TransientModel):
    _name = 'report.report_custom_product_catalog.catalog_temp'

    def _get_report_values(self, docids, data=None):
        popup = self.env['popup.custom.product.catalog'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        context = {}
        if popup.start_date or popup.end_date:
            product_list = self.fetchData(popup)
            context = {'production_lot_ids': product_list[0][1]}
        return {'data': self.env['product.product'].with_context(context).browse(docids)}

    def fetchData(self,ctx):
        sql_query = """select array_agg(product_id), json_object_agg(product_id, id) from stock_lot 
        where """
        if ctx.end_date and ctx.start_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            sql_query = sql_query + """ use_date>=date(%s)  and  use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(ctx.start_date), str(e_date),))
        elif ctx.start_date:
            sql_query = sql_query + """ use_date>=date(%s) """
            ctx._cr.execute(sql_query, (str(ctx.start_date),))
        elif ctx.end_date:
            e_date = datetime.datetime.strptime(str(ctx.end_date), "%Y-%m-%d")
            e_date = e_date + datetime.timedelta(days=1)
            sql_query = sql_query + """ use_date<=date(%s)"""
            ctx._cr.execute(sql_query, (str(e_date),))

        return ctx._cr.fetchall()


    def download_excel_product_catalog(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/ProductCatalog/download_document_xl',
            'target': 'new'
        }
        # if check_product_catalog_export == 0:
        #     global check_product_catalog_export
        #     check_product_catalog_export = 1
        #     list_val = self.get_excel_data_product_catalog()
        #
        #     if list_val and len(list_val) > 0:
        #         return {
        #             'type': 'ir.actions.act_url',
        #             'url': '/web/ProductCatalog/download_document_xl',
        #             'target': 'new'
        #         }
        #     else:
        #         product_catalog_export.clear()
        #         check_product_catalog_export = 0
        #         raise UserError(
        #             _('Cannot Export at the moment ,Please try after sometime.'))

    # def get_excel_data_product_catalog(self):
    #
    #     count = 0
    #     product_catalog_export.append((['Product Type', 'Product SKU', 'Product Name','Manufacture','Price']))
    #
    #     str_query = """
    #                 select pt.type,pt.default_code  ,pt.name,pb.name as manufacture,pt.list_price
    #                 from product_template as pt left join product_brand as pb
    #                 on pt.product_brand_id = pb.id
    #
    #                 """
    #
    #     self.env.cr.execute(str_query)
    #     new_list = self.env.cr.dictfetchall()
    #
    #     for line in new_list:
    #         count = count + 1  # for printing count if needed
    #         product_catalog_export.append(
    #             ([line['type'], line['default_code'], line['name'], line['manufacture'],
    #               line['list_price']]))
    #
    #     return product_catalog_export


class ProductCatalogXL(http.Controller):

    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   XL will be

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self):
        return 'ProductCatalog' + '.xls'

    def from_data(self, field, rows):
        if len(rows) > 65535:
            raise UserError(_(
                'There are too many rows (%s rows, limit: 65535) to export as Excel 97-2003 (.xls) format. Consider splitting the export.') % len(
                rows))

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        for i, fieldname in enumerate(field):
            worksheet.write(0, i, fieldname)
            if i == 2:
                worksheet.col(i).width = 20000  #
            else:
                worksheet.col(i).width = 4000  # around 110 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style

                if isinstance(cell_value, bytes) and not isinstance(cell_value, str):
                    # because xls uses raw export, we can get a bytes object
                    # here. xlwt does not support bytes values in Python 3 ->
                    # assume this is base64 and decode to a string, if this
                    # fails note that you can't export
                    try:
                        cell_value = pycompat.to_text(cell_value)
                    except UnicodeDecodeError:
                        raise UserError(_(
                            "Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") %
                                        fields[cell_index])

                if isinstance(cell_value, str):
                    cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                    # Excel supports a maximum of 32767 characters in each cell:
                    cell_value = cell_value[:32767]
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

    @http.route('/web/ProductCatalog/download_document_xl', type='http', auth="public")
    def download_document_xl(self, token=1, debug=1):

        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added

        product_catalog_export = []
        try:
            # list_val = self.get_excel_data_product_catalog()
            # if list_val and len(list_val) > 0:

            str_query = "  select sku as default_code, manufacture   ,name  , qty as actual_quantity ,list_price ,min_date  as min_expiration_date , max_date as max_expiration_date from cust_pro_catalog WHERE user_id = '"+str(request.context['uid'])+"'"
            request.env.cr.execute(str_query)
            order_lines = request.env.cr.dictfetchall()

            product_catalog_export.append((['Manufacture','Product SKU','Product Name',
                                            'Product Qty','Price','Min Exp Date','Max Exp Date']))

            for line in order_lines:
                product_catalog_export.append(([line['manufacture'],line['default_code'],  line['name'],
                                                line['actual_quantity'],line['list_price'],line['min_expiration_date'],
                                                line['max_expiration_date']]))

            res = request.make_response(self.from_data(product_catalog_export[0], product_catalog_export[1:]),
                                        headers=[('Content-Disposition',
                                                  content_disposition(self.filename())),
                                                 ('Content-Type', self.content_type)],
                                        )
            product_catalog_export.clear()
            return res

        except:
            res = request.make_response('', '')
            product_catalog_export.clear()
            return res


class ReportProductWise(models.AbstractModel):
    _name = 'report.report_custom_product_catalog.product_catalog_temp'

    def _get_report_values(self, docids, data=None):
        return {'data': self.env['product.product'].browse(docids)}