# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportRevenueByBdPerAccount(http.Controller):

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

                    if isinstance(cell_value, bytes) and not isinstance(cell_value, str):

                        try:
                            cell_value = pycompat.to_text(cell_value)
                        except UnicodeDecodeError:
                            raise UserError(_(
                                "Binary fields can not be exported to Excel unless their content is base64-encoded. That "
                                "does not seem to be the case for %s.") %
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

    @http.route('/web/export/revenue_by_bd_per_account_export/<string:start_date>/<string:end_date>/<string:salesperson_account_id>',
                type='http',
                auth="public")
    def download_document_xl(self, start_date, end_date, salesperson_account_id, token=1, debug=1, **kw):

        select_query = """
                SELECT
                       ROW_NUMBER () OVER (ORDER BY SO.id)      AS id, 
                       SO.name                                  AS sale_order_id,
                       MAX(SP.date_done)                        AS delivery_date,
                       RP.name                                  AS business_development,
                       ResPartner.name                          AS customer,
                       SO.state                                 AS status,
                       SUM(SOL.qty_delivered * SOL.price_reduce)  AS total_amount 

                FROM public.sale_order SO
                INNER JOIN 
                    public.sale_order_line SOL 
                ON 
                    SO.id = SOL.order_id
                INNER JOIN 
                        (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin)
                    AS SP 
                ON 
                    SO.id = SP.sale_id
                INNER JOIN 
                    public.res_users RU 
                ON 
                    (
                        SO.user_id = RU.id)
                INNER JOIN 
                    public.res_partner RP 
                ON
                    ( 
                        RU.partner_id = RP.id)
                INNER JOIN 
                    public.res_partner ResPartner 
                ON
                    ( 
                        SO.partner_id = ResPartner.id AND (ResPartner.is_wholesaler is NULL OR ResPartner.is_wholesaler != TRUE) 
                        AND (ResPartner.is_broker is NULL OR ResPartner.is_broker != TRUE))


                   WHERE SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL

               """

        if start_date != "all" and end_date != "all":
            select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"

        if salesperson_account_id != "none":
            select_query = select_query + "AND SO.user_id = '" + str(salesperson_account_id) + "'"

        group_by = """
                           GROUP BY
                            SO.id, RP.name, ResPartner.name
                            ORDER BY RP.name             
                               """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['sale_order_id'],
                            line['customer'], line['business_development'],
                            line['delivery_date'],
                            line['total_amount']])

        res = request.make_response(
            self.from_data(["Sale Order#", "Customer Name", "Business Development", "Delivery Date", "Total"],
                           records),
            headers=[('Content-Disposition', content_disposition('revenue_by_bd_per_account' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
