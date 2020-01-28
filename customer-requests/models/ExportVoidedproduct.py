import json
import logging
from odoo import models, fields, api, _, http
import io
import re
import datetime
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, xlwt
_logger = logging.getLogger(__name__)


class VoidedproductExport(models.TransientModel):
    _name = 'voided.product.export'
    _description = 'Voided Product Export'

    def download_excel_voided_product(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/VoidedProduct/download_voided_product_xl',
            'target': 'new'
        }


class VoidedProductXL(http.Controller):
    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   XL will be

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

                if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
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

                if isinstance(cell_value, pycompat.string_types):
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

    @http.route('/web/VoidedProduct/download_voided_product_xl', type='http', auth="public")
    @serialize_exception
    def download_document_xl(self, token=1, debug=1):
        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added
        voided_requests = request.env['sps.customer.requests'].search([('status', '=', 'Voided')])
        try:
            records = []
            for line in voided_requests:
                if line.required_quantity:
                    quantity = line.required_quantity
                else:
                    quantity = line.quantity
                price = False
                if line.un_mapped_data:
                    un_mapped_dict = line.un_mapped_data.lower()
                    if 'cost' in json.loads(un_mapped_dict):
                        price = json.loads(un_mapped_dict).get('cost')
                records.append([line.customer_id.name, line.document_id.document_name, line.product_description,
                                line.customer_sku, quantity, price, line.status])
            res = request.make_response(
                self.from_data(["Customer Name", "Document Name", "Product Description", "Customer SKU",
                                "Quantity Requested", "Price", "Status"], records),
                headers=[('Content-Disposition', content_disposition('voided_products' + '.xls')),
                         ('Content-Type', 'application/vnd.ms-excel')],)
            records.clear()
            return res
        except:
            res = request.make_response('', '')
            records.clear()
            return res
