# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportAccountClosedByBd(http.Controller):

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

    @http.route('/web/export/account_closed_by_bd_export/<string:start_date>/<string:end_date>/<string:business_development_id>',
                type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date, business_development_id, token=1, debug=1, **kw):

        select_query = """
                    SELECT 
                        ROW_NUMBER () OVER (ORDER BY SOS.id)    AS id,
                        SOS.name                                AS sale_order_id,
                        RPS.name                                AS customer, 
                        RPSS.name                               AS business_development, 
                        MAX(SPS.date_done)                      AS delivery_date, 
                        SOS.state                               AS state,
                        SUM(SOL.qty_delivered * SOL.price_reduce) AS total_amount
                    FROM public.sale_order SOS
                    INNER JOIN public.res_users RU ON SOS.user_id = RU.id
                    INNER JOIN public.res_partner RPSS ON RU.partner_id = RPSS.id
                    INNER JOIN public.sale_order_line SOL ON SOS.id = SOL.order_id 
                    INNER JOIN public.res_partner RPS ON SOS.partner_id = RPS.id
                    INNER JOIN public.stock_picking SPS ON SOS.id = SPS.sale_id AND SPS.picking_type_id = 5 AND SPS.state = 'done'
                    WHERE SOS.state NOT IN ('cancel', 'void') AND SOS.user_id IS NOT NULL AND SOS.partner_id IN 
                    ((SELECT DISTINCT (SO.partner_id) partner1
                    FROM public.sale_order SO
                    INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                    WHERE """

        select_query = select_query + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
            start_date) + "' " + """ AND SP.state = 'done'
                    AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                        SELECT DISTINCT (SO.partner_id) partner
                        FROM public.sale_order SO
                        INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
                        WHERE """

        select_query = select_query + " SP.date_done <= '" + str(end_date) + "' " \
                       + """ AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')
                    ))UNION ALL
                    (SELECT DISTINCT (SO.partner_id) partner1
                    FROM public.sale_order SO
                    INNER JOIN public.stock_picking SP ON SO.id IN (
                        Select SO.id
                        From public.sale_order SO
                        INNER JOIN public.stock_picking SP 
                        ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 
                                      AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                        WHERE SO.partner_id IN (
                                SELECT id
                                FROM public.res_partner RP
                                WHERE RP.rejoin_date IS NOT NULL AND """

        select_query = select_query + " RP.rejoin_date BETWEEN '" + str(end_date) + "'" + " AND '" + str(
            start_date) + "' )) WHERE " + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
            start_date) + "' " + """ AND SP.state = 'done' AND SP.picking_type_id = 5 
                    AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
                            SELECT DISTINCT (SO.partner_id) partner
                            FROM public.sale_order SO        
                            INNER JOIN public.stock_picking SP ON SO.id IN (        
                                    Select SO.id
                                    From public.sale_order SO
                                    INNER JOIN public.stock_picking SP 
                                    ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5 
                                                  AND SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL
                                    WHERE SO.partner_id IN (
                                            SELECT id 
                                            FROM public.res_partner RP
                                            WHERE RP.rejoin_date IS NOT NULL AND 

                """

        select_query = select_query + " RP.rejoin_date <= '" + str(end_date) + "' ) ) WHERE SP.date_done <= '" + str(
            end_date) + " ' " \
                        " AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')))) "

        select_query = select_query + " AND SPS.date_done >= COALESCE(RPS.rejoin_date, RPS.create_date) " \
                                      " AND SPS.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
            start_date) + "'"

        if business_development_id != "none":
            select_query = select_query + "AND SOS.user_id = '" + str(business_development_id) + "'"

        group_by = """ GROUP BY SOS.id, SOS.name, RPS.name, RPSS.name, SPS.date_done, SOS.state """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['sale_order_id'],
                            line['customer'], line['business_development'],
                            line['delivery_date'],
                            line['state'],
                            line['total_amount']])

        res = request.make_response(
            self.from_data(["Sale Order#", "Customer Name", "Business Development", "Delivery Date", "Status", "Total"],
                           records),
            headers=[('Content-Disposition', content_disposition('account_closed_by_bd' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
