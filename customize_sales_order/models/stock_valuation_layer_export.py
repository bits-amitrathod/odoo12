import time
from odoo import models, fields
from odoo.exceptions import UserError
import io
import logging
import re
import xlwt
import xlsxwriter
import datetime
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.tools import pycompat
from xlsxwriter.worksheet import Worksheet

_logger = logging.getLogger(__name__)

try:
    class PatchedWorkbook(xlsxwriter.Workbook):
        def add_sheet(self, name):
            # Invalid Excel characters for sheet names: []:*?/\
            name = re.sub(r'[\[\]:*?/\\]', '', name)
            # Maximum sheet name size is 31 characters
            name = name[:31]
            return self.add_worksheet(name)

    xlsxwriter.Workbook = PatchedWorkbook

except ImportError:
    xlsxwriter = None

all_field_import = 'all_field_import'

SUPERUSER_ID_INFO = 2

product_lines_export_stock = []

class StockValuationReport(models.Model):
    _inherit = 'stock.valuation.layer'
    _description = 'Stock Valuation Layer'

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company
    )
    product_id = fields.Many2one(
        'product.product',
        required=True,
        default=lambda self: self.env['product.product'].search([], limit=1)
    )

    def get_excel_data_stock_valuation(self):
        product_lines_lines_export_stock = [
           ['Company', 'Created On', 'Product', 'Quantity', 'Total Value', 'Reference', 'Unit Value', 'Unit Of Measure']
        ]

        company = self.env.company
        logging.info("Execution time before query:")
        query = """
                SELECT 
                    svl.company_id as company_id,
                    rc.name as company_name,
                    svl.create_date as create_date,
                    svl.product_id as product_id,
                    pt.name -> 'en_US' as product_name,
                    svl.quantity as quantity,
                    svl.value as value,
                    sm.reference as reference,
                    unit_cost as unit_cost,
                    uu.name -> 'en_US' as uom_name
                 FROM  stock_valuation_layer as svl
                 LEFT JOIN stock_move sm on stock_move_id = sm.id 
                 LEFT JOIN product_product pp on svl.product_id =pp.id
                 LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
                 LEFT JOIN uom_uom uu on uu.id = pt.uom_id
                 LEFT JOIN res_company rc on rc.id = svl.company_id  """

        self.env.cr.execute(query, (company.id,))
        results = self.env.cr.dictfetchall()
        logging.info("Execution time after query:")
        logging.info("Execution time before for loop:")
        for line in results:
            product_lines_lines_export_stock.append([
                line['company_name'],
                line['create_date'],
                line['product_name'],
                line['quantity'],
                line['value'],
                line['reference'],
                line['unit_cost'],
                line['uom_name'],
            ])
        logging.info("Execution time after for loop:")
        return product_lines_lines_export_stock


    def download_excel_stock_valuation(self):
        list_val = self.get_excel_data_stock_valuation()
        if list_val and len(list_val) > 0:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/StockValuation/download_document_xl',
                'target': 'new'
            }
        else:
            product_lines_export_stock.clear()
            raise UserError(_('Cannot Export at the moment, Please try after sometime.'))


class ExportStockValuationXL(http.Controller):
    @property
    def content_type(self):
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def filename(self):
        return 'Stock Valuation Layer.xlsx'

    # Function to generate the Excel file
    def from_data(self, field, rows):
        try:
            # Create an in-memory output file for the new workbook.
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Sheet 1')

            # Define styles
            base_format = workbook.add_format({'text_wrap': True})
            date_format = workbook.add_format({'text_wrap': True, 'num_format': 'yyyy-mm-dd'})
            datetime_format = workbook.add_format({'text_wrap': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'})

            # Write the header
            for i, fieldname in enumerate(field):
                worksheet.write(0, i, fieldname, base_format)
                if i == 1:
                    worksheet.set_column(i, i, 20)  # Set column width for column `i` to 20 characters
                else:
                    worksheet.set_column(i, i, 40)  # Default width for other columns

            # Write the data rows
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    cell_format = base_format

                    if isinstance(cell_value, bytes):
                        try:
                            cell_value = cell_value.decode('utf-8')
                        except UnicodeDecodeError:
                            raise ValueError("Binary fields must be base64-encoded.")

                    if isinstance(cell_value, str):
                        cell_value = re.sub("\r", " ", cell_value)
                        # Limit to 32767 characters
                        cell_value = cell_value[:32767]
                    elif isinstance(cell_value, datetime.datetime):
                        cell_format = datetime_format
                    elif isinstance(cell_value, datetime.date):
                        cell_format = date_format
                    elif isinstance(cell_value, dict) and 'en_US' in cell_value:
                        cell_value = cell_value.get('en_US') or cell_value.get(list(cell_value.keys())[0]) or ''

                    worksheet.write(row_index + 1, cell_index, cell_value, cell_format)

            # Close the workbook
            workbook.close()

            # Get the data from the in-memory file
            output.seek(0)
            data = output.read()
            output.close()
            return data
        except Exception as ex:
            _logger.error("Error generating Excel file: %s", ex)
            raise

    @http.route('/web/StockValuation/download_document_xl', type='http', auth="user")
    def download_document_xl(self, **kwargs):
        try:
            stock_valuation = request.env['stock.valuation.layer'].sudo()
            data = stock_valuation.get_excel_data_stock_valuation()

            response = request.make_response(
                self.from_data(data[0], data[1:]),
                headers=[
                    ('Content-Disposition', content_disposition(self.filename())),
                    ('Content-Type', self.content_type)
                ]
            )
            return response
        except Exception as e:
            return request.not_found()


