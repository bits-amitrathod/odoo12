# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class StockedProductSoldByKa(http.Controller):

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

    @http.route('/web/export/revenue_by_ka_export/<string:start_date>/<string:end_date>/<string:key_account_id>'
                '/<string:date_difference>', type='http', auth="public")
    def download_document_xl(self, start_date, end_date, key_account_id, date_difference, token=1, debug=1, **kw):

        select_query = """
                        SELECT 
                            ROW_NUMBER () OVER (ORDER BY RP.id)         AS id, 
                            RP.name                                     AS customer, 
                            RPS.name                                    AS key_account,
                            CASE WHEN SOL.currency_id is NULL THEN 3 ELSE SOL.currency_id  END AS currency_id,
                            CASE WHEN COUNT(SO.no_of_order) > 0 THEN COUNT(SO.no_of_order) ELSE 0 END AS no_of_orders,
                            CASE WHEN SUM(SOL.revenue) > 0 THEN SUM(SOL.revenue) ELSE 0 END AS total_revenue,

                            """
        select_query = select_query + " CASE WHEN RP.order_quota > 0 THEN RP.order_quota*" + \
                       str(date_difference) + " ELSE 0 END AS order_quota, " + \
                       " CASE WHEN RP.order_quota > 0 THEN (COUNT(SO.no_of_order)/(RP.order_quota*" + \
                       str(date_difference) + "))*100 ELSE 0 END AS progress_order_quota," + \
                       " CASE WHEN RP.revenue_quota > 0 THEN RP.revenue_quota *" + str(date_difference) + \
                       " ELSE 0 END AS revenue_quota," + \
                       " CASE WHEN RP.revenue_quota > 0 THEN SUM(SOL.revenue)/(RP.revenue_quota*" + str(
            date_difference) + \
                       ")*100 ELSE 0 END AS progress_revenue_quota"

        select_query = select_query + """

                        FROM public.res_partner RP
                        
                        INNER JOIN 
                            public.res_users RU
                        ON
                            RP.account_manager_cust = RU.id
                        INNER JOIN 
                            public.res_partner RPS
                        ON 
                            RU.partner_id = RPS.id

                        LEFT JOIN 
                            (SELECT id, COUNT(sale_order.id) AS no_of_order, sale_order.partner_id, sale_order.create_date 
                                FROM public.sale_order sale_order
                            LEFT JOIN (SELECT DISTINCT ON (origin) origin, date_done, sale_id 
                                FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin) AS SP 
                            ON sale_order.id = SP.sale_id
                            WHERE state not in ('cancel', 'void') AND """

        select_query = select_query + "SP.date_done >= '" + str(start_date) + "' AND SP.date_done <= '" + \
                       str(end_date) + "'"

        select_query = select_query + """   GROUP BY id, partner_id) AS SO ON RP.id = SO.partner_id

                        LEFT JOIN 
                            (SELECT DISTINCT ON (order_id) order_id, SUM(qty_delivered * price_reduce) AS revenue, currency_id 
                                FROM sale_order_line
                                GROUP BY order_id, currency_id) AS SOL ON SO.id = SOL.order_id

                        WHERE RP.account_manager_cust IS NOT NULL          

                    """

        if key_account_id != "none":
            select_query = select_query + "AND RP.account_manager_cust = '" + str(key_account_id) + "'"

        group_by = """
                                GROUP BY
                                    RP.id, RPS.name, SO.no_of_order, SOL.currency_id
                                    
                                    ORDER BY RPS.name
                                    """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            if line['progress_order_quota'] > 0 and line['progress_revenue_quota'] > 0:
                records.append([line['customer'], line['key_account'],
                            line['no_of_orders'], line['order_quota'], round(line['progress_order_quota'], 2),
                            line['total_revenue'], line['revenue_quota'], round(line['progress_revenue_quota'], 2)])
            else:
                records.append([line['customer'], line['key_account'],
                                line['no_of_orders'], line['order_quota'], line['progress_order_quota'],
                                line['total_revenue'], line['revenue_quota'], line['progress_revenue_quota']])

        res = request.make_response(
            self.from_data(["Customer Name", "Key Account", "No. of orders", "Order Quota", "Progress of Order Quota",
                            "Total Revenue", "Revenue Quota", "Progress of Revenue Quota"],
                           records),
            headers=[('Content-Disposition', content_disposition('revenue_by_ka' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
