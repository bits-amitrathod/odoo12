# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportNewAccountByMonthByNa(http.Controller):

    def from_data(self, field, rows):
        split_data = []
        limit = 65530
        # 65535
        if len(rows) > limit:
            count = math.ceil(len(rows) / limit)
            index = 0
            max = limit
            for loop in range(count):
                split_data.append(rows[index:max])
                index = index + limit
                max = max + limit
        else:
            split_data.append(rows)

        workbook = xlwt.Workbook()
        count = 1
        for data in split_data:
            worksheet = workbook.add_sheet('Sheet ' + str(count))
            count = count + 1

            for i, fieldname in enumerate(field):
                worksheet.write(0, i, fieldname)
                if i == 5:
                    worksheet.col(i).width = 15500  #
                elif i == 1:
                    worksheet.col(i).width = 10000  #
                else:
                    worksheet.col(i).width = 4700  # around 110 pixels

            base_style = xlwt.easyxf('align: wrap yes')
            date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
            datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

            for row_index, row in enumerate(data):
                for cell_index, cell_value in enumerate(row):
                    cell_style = base_style

                    if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):

                        try:
                            cell_value = pycompat.to_text(cell_value)
                        except UnicodeDecodeError:
                            raise UserError(_(
                                "Binary fields can not be exported to Excel unless their content is base64-encoded. That "
                                "does not seem to be the case for %s.") %
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

    @http.route('/web/export/new_account_by_month_by_na_export/<string:start_date>/<string:end_date>/<string:national_account_id>',
                type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date, national_account_id, token=1, debug=1, **kw):

        select_query = """
                       SELECT
                            ROW_NUMBER () OVER (ORDER BY RP.id) AS id,
                            RP.name                             AS customer,
                            COALESCE(RP.reinstated_date, RP.create_date)        AS onboard_date,
                            RPS.name                                            AS national_account
            
                       FROM public.res_partner RP
                        
                        INNER JOIN 
                            public.res_users RU 
                        ON 
                            (
                              RP.national_account_rep = RU.id)
                        INNER JOIN
                              public.res_partner RPS
                        ON 
                            (
                                RU.partner_id = RPS.id)
            
                        WHERE RP.customer = true AND RP.active = true 
                        AND RP.national_account_rep IS NOT NULL AND RP.parent_id IS NULL

          """


        if start_date != "all" and end_date != "all":
            select_query = select_query + " AND COALESCE(RP.reinstated_date, RP.create_date) BETWEEN '" + str(
                start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"

        if national_account_id != "none":
            select_query = select_query + "AND RP.national_account_rep = '" + str(national_account_id) + "'"

        order_by = """ ORDER BY RPS.name"""

        select_query = select_query + order_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([
                            line['customer'],
                            line['onboard_date'],
                            line['national_account']])

        res = request.make_response(
            self.from_data(["Customer Name", "Onboard Date", "National Account"],
                           records),
            headers=[('Content-Disposition', content_disposition('new_account_by_month_by_na' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()