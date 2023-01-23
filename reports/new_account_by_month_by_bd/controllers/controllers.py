# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from dateutil.relativedelta import relativedelta
import datetime
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportNewAccountByMonthByBd(http.Controller):

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

    @http.route('/web/export/new_account_by_month_by_bd_export/<string:start_date>/<string:end_date>/<string:business_development_id>',
                type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date, business_development_id, token=1, debug=1, **kw):

        s_date = self.string_to_date(start_date)
        today = s_date if s_date else fields.date.today()
        internal_date = (today - relativedelta(months=24))

        select_query = """
                        SELECT 
                            ROW_NUMBER () OVER (ORDER BY RPS.id)    AS id,
                            RPS.name                                AS customer, 
                            RPSS.name                               AS business_development, 
                            MIN(SPS.date_done)                      AS onboard_date
                        FROM public.sale_order SOS 
                        INNER JOIN 
                            public.res_partner RPS 
                        ON 
                            SOS.partner_id = RPS.id AND (RPS.is_wholesaler is NULL OR RPS.is_wholesaler != TRUE) 
                            AND (RPS.is_broker is NULL OR RPS.is_broker != TRUE)
                        INNER JOIN 
                            public.stock_picking SPS 
                        ON 
                            SOS.id = SPS.sale_id AND SPS.picking_type_id = 5 AND SPS.state = 'done'

                        INNER JOIN 
                            public.res_users RU 
                        ON 
                            SOS.user_id = RU.id
                        INNER JOIN
                              public.res_partner RPSS
                        ON 
                            RU.partner_id = RPSS.id

                        WHERE SOS.user_id IS NOT NULL AND SOS.state NOT IN ('cancel', 'void') AND SOS.partner_id IN

                        ((  SELECT 
                                DISTINCT (SO.partner_id) partner1
                            FROM 
                                public.sale_order SO
                            INNER JOIN 
                                public.stock_picking SP 
                            ON 
                                SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND

                           """
        select_query = select_query + " SP.date_done BETWEEN '" + str(start_date) + "'" + " AND '" + str(
            end_date) + "' " + """ WHERE SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                        SELECT 
                            DISTINCT (SO.partner_id) partner
                        FROM 
                            public.sale_order SO
                        INNER JOIN 
                            public.stock_picking SP ON SO.id = SP.sale_id AND SP.state = 'done' AND 
                            SP.picking_type_id = 5 AND SP.date_done BETWEEN ' """ + str(internal_date) + """'""" + """ AND ' """ + str(today) + """ ' 
                            WHERE SO.state NOT IN ('cancel', 'void'))) UNION ALL ("""

        select_query = select_query + """ 
                    SELECT 
                        DISTINCT (SO.partner_id) partner1
                    FROM 
                        public.sale_order SO 
                    WHERE SO.id IN (
                        SELECT SO.id
                        FROM 
                            public.sale_order SO
                        INNER JOIN 
                            public.stock_picking SP 
                        ON 
                            SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND SP.date_done BETWEEN ' """ + \
                       str(start_date) + "' " + " AND '" + str(end_date) + \
                       """ ' AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                   WHERE SO.partner_id IN (
                           SELECT id
                           FROM public.res_partner RP
                           WHERE RP.reinstated_date IS NOT NULL AND RP.reinstated_date BETWEEN ' """ + \
                       str(start_date) + "'" + " AND '" + str(end_date) + "' ) ) AND SO.partner_id NOT IN ("

        select_query = select_query + """ 
                        SELECT 
                            DISTINCT (SO.partner_id) partner
                        FROM 
                            public.sale_order SO        
                        WHERE SO.id IN (        
                                Select SO.id
                                From public.sale_order SO
                                INNER JOIN public.stock_picking SP 
                                ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 AND SP.date_done <= ' """ + \
                       str(start_date) + "' " + \
                       """ AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                       WHERE SO.partner_id IN (
                               SELECT id 
                               FROM public.res_partner RP
                               WHERE RP.reinstated_date IS NOT NULL AND RP.reinstated_date <= '""" + str(start_date) + \
                       "' ) ) ))) AND SPS.date_done" \
                       " >= COALESCE(RPS.reinstated_date, RPS.create_date) AND SPS.date_done BETWEEN '" + \
                       str(start_date) + "'" + " AND '" + str(end_date) + "' "

        if business_development_id != "none":
            select_query = select_query + "AND SOS.user_id = '" + str(business_development_id) + "'"

        group_by = """ GROUP BY RPS.id, RPS.name, RPSS.name  
                        ORDER BY RPSS.name """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([
                            line['customer'],
                            line['onboard_date'],
                            line['business_development']])

        res = request.make_response(
            self.from_data(["Customer Name", "Delivery Date", "Business Development"],
                           records),
            headers=[('Content-Disposition', content_disposition('new_account_by_month_by_bd' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
