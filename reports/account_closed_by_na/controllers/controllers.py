# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportAccountClosedByNa(http.Controller):

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

    @http.route(
        '/web/export/account_closed_by_na_export/<string:start_date>/<string:end_date>/<string:national_account_id>/'
        '<string:delivery_start_date>/<string:delivery_end_date>',
        type='http',
        auth="public")
    def download_document_xl(self, start_date, end_date, national_account_id, delivery_start_date, delivery_end_date,
                             token=1, debug=1, **kw):

        select_query = """
                        SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                                so.id                               AS sale_order_id, 
                                so.partner_id                       AS customer, 
                                so.national_account                 AS national_account, 
                                so.account_manager                  AS key_account,
                                so.state                            AS state,
                                MAX(SPS.date_done)                  AS delivery_date, 
                                rp.account_manager_cust             AS customer_key_account,
                                ai.invoice_date                     AS invoice_date, 
                                CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                                CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                                SUM(SOL.qty_delivered * SOL.price_reduce)                   AS total_amount, 
                                X.months                            AS months,
                                ai.currency_id                      AS currency_id,
                                X.first_occurence                   AS date_of_first_order
                        FROM public.sale_order so
                        INNER JOIN
                           (
                            (SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                                    DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                                FROM public.sale_order sos
                                INNER JOIN 
                                    public.account_move aii ON sos.name = aii.invoice_origin
                                GROUP BY sos.partner_id
                                Having MIN(aii.invoice_date) > '""" + str(end_date) + """ ')

                                UNION

                                ( SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                                    DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                                FROM public.sale_order sos 
                                INNER JOIN public.res_partner rep ON sos.partner_id= rep.id 
                                INNER JOIN public.account_move aii ON sos.name = aii.invoice_origin 
                                where rep.reinstated_date > ' """ + str(end_date) + """ ' and rep.reinstated_date is not null

                                and  aii.invoice_date > ' """ + str(end_date) + """ '  GROUP BY sos.partner_id )

                            ) X
                                ON so.partner_id = X.partner_id
                            INNER JOIN 
                                public.account_move ai ON so.name = ai.invoice_origin AND ai.state in ('posted')
                            INNER JOIN 
                                public.res_partner rp ON so.partner_id = rp.id

                            INNER JOIN public.sale_order_line SOL ON so.id = SOL.order_id 
                            INNER JOIN 
                            (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 
                            AND state = 'done' ORDER BY origin) AS SPS 
                            ON so.id = SPS.sale_id
                            INNER JOIN  public.product_product  pp on SOL.product_id = pp.id 
                    INNER JOIN  public.product_template  pt on pp.product_tmpl_id = pt.id and pt.type!='service'

                        WHERE so.invoice_status = 'invoiced'                
                           """

        select_query = select_query + " AND SPS.date_done >= COALESCE(rp.reinstated_date, ai.invoice_date,rp.create_date) " \
                                      " AND SPS.date_done BETWEEN '" + str(end_date) + "' " + " AND '" + str(
            start_date) + "' AND SPS.date_done <= (COALESCE(rp.reinstated_date, ai.invoice_date,rp.create_date) + " \
                          "INTERVAL '18 month')  "

        if national_account_id:
            select_query = select_query + "AND so.national_account = '" + str(national_account_id) + "'"

        group_by = """ GROUP BY so.id, SPS.date_done, SOL.currency_id,so.national_account, rp.account_manager_cust,
                      X.months  ,X.first_occurence ,ai.invoice_date,ai.state,ai.currency_id  """

        select_query = select_query + group_by

        order_by = " ORDER BY ai.invoice_date asc"

        select_query = select_query + order_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        if delivery_start_date != 'none' and delivery_end_date != 'none':
            for line in order_lines:
                if line['delivery_date'].date() >= self.string_to_date(delivery_start_date) and \
                        line['delivery_date'].date() <= self.string_to_date(delivery_end_date):
                    records.append([line['sale_order_id'],
                                    line['customer'], line['national_account'],
                                    line['delivery_date'],
                                    line['state'],
                                    line['total_amount']])
        else:
            for line in order_lines:
                records.append([line['sale_order_id'],
                                line['customer'], line['national_account'],
                                line['delivery_date'],
                                line['state'],
                                line['total_amount']])

        res = request.make_response(
            self.from_data(["Sale Order#", "Customer Name", "National Account", "Delivery Date", "Status", "Total"],
                           records),
            headers=[('Content-Disposition',
                      content_disposition('revenue_from_accounts_closed_in_12_months_by_na' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    # @http.route('/web/export/account_closed_by_na_export/<string:start_date>/<string:end_date>/<string:national_account_id>/'
    #             '<string:delivery_start_date>/<string:delivery_end_date>',
    #             type='http',
    #             auth="public")
    # def download_document_xl(self, start_date, end_date, national_account_id, delivery_start_date, delivery_end_date,
    #                          token=1, debug=1, **kw):
    #
    #     select_query = """
    #                 SELECT
    #                     ROW_NUMBER () OVER (ORDER BY SOS.id)    AS id,
    #                     SOS.name                                AS sale_order_id,
    #                     RPS.name                                AS customer,
    #                     RPSS.name                               AS national_account,
    #                     MAX(SPS.date_done)                      AS delivery_date,
    #                     SOS.state                               AS state,
    #                     SUM(SOL.qty_delivered * SOL.price_reduce) AS total_amount
    #                 FROM public.sale_order SOS
    #                 INNER JOIN public.res_users RU ON SOS.national_account = RU.id
    #                 INNER JOIN public.res_partner RPSS ON RU.partner_id = RPSS.id
    #                 INNER JOIN public.sale_order_line SOL ON SOS.id = SOL.order_id
    #                 INNER JOIN public.res_partner RPS ON SOS.partner_id = RPS.id AND
    #                 (RPS.is_wholesaler is NULL OR RPS.is_wholesaler != TRUE) AND (RPS.is_broker is NULL OR RPS.is_broker != TRUE)
    #                 INNER JOIN
    #                 (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 AND state = 'done' ORDER BY origin) AS SPS
    #                 ON SOS.id = SPS.sale_id
    #                 WHERE SOS.state NOT IN ('cancel', 'void') AND SOS.national_account IS NOT NULL AND SOS.partner_id IN
    #                 ((SELECT DISTINCT (SO.partner_id) partner1
    #                 FROM public.sale_order SO
    #                 INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
    #                 WHERE """
    #
    #     select_query = select_query + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
    #         start_date) + "' " + """ AND SP.state = 'done'
    #                 AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
    #                     SELECT DISTINCT (SO.partner_id) partner
    #                     FROM public.sale_order SO
    #                     INNER JOIN public.stock_picking SP ON SO.id = SP.sale_id
    #                     WHERE """
    #
    #     select_query = select_query + " SP.date_done <= '" + str(end_date) + "' " \
    #                    + """ AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')
    #                 ))UNION ALL
    #                 (SELECT DISTINCT (SO.partner_id) partner1
    #                 FROM public.sale_order SO
    #                 INNER JOIN public.stock_picking SP ON SO.id IN (
    #                     Select SO.id
    #                     From public.sale_order SO
    #                     INNER JOIN public.stock_picking SP
    #                     ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5
    #                                   AND SO.state NOT IN ('cancel', 'void') AND SO.national_account IS NOT NULL
    #                     WHERE SO.partner_id IN (
    #                             SELECT id
    #                             FROM public.res_partner RP
    #                             WHERE RP.reinstated_date IS NOT NULL AND """
    #
    #     select_query = select_query + " RP.reinstated_date BETWEEN '" + str(end_date) + "'" + " AND '" + str(
    #         start_date) + "' )) WHERE " + " SP.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
    #         start_date) + "' " + """ AND SP.state = 'done' AND SP.picking_type_id = 5
    #                 AND SO.state NOT IN ('cancel', 'void') AND SO.partner_id NOT IN (
    #                         SELECT DISTINCT (SO.partner_id) partner
    #                         FROM public.sale_order SO
    #                         INNER JOIN public.stock_picking SP ON SO.id IN (
    #                                 Select SO.id
    #                                 From public.sale_order SO
    #                                 INNER JOIN public.stock_picking SP
    #                                 ON SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5
    #                                               AND SO.state NOT IN ('cancel', 'void') AND SO.national_account IS NOT NULL
    #                                 WHERE SO.partner_id IN (
    #                                         SELECT id
    #                                         FROM public.res_partner RP
    #                                         WHERE RP.reinstated_date IS NOT NULL AND
    #
    #             """
    #
    #     select_query = select_query + " RP.reinstated_date <= '" + str(end_date) + "' ) ) WHERE SP.date_done <= '" + str(
    #         end_date) + " ' " \
    #                     " AND SP.state = 'done' AND SP.picking_type_id = 5 AND SO.state NOT IN ('cancel', 'void')))) "
    #
    #     select_query = select_query + " AND SPS.date_done >= COALESCE(RPS.reinstated_date, RPS.create_date) " \
    #                                   " AND SPS.date_done BETWEEN '" + str(end_date) + "'" + " AND '" + str(
    #         start_date) + "'"
    #
    #     if national_account_id != "none":
    #         select_query = select_query + "AND SOS.national_account = '" + str(national_account_id) + "'"
    #
    #     group_by = """ GROUP BY SOS.id, SOS.name, RPS.name, RPSS.name, SPS.date_done, SOS.state ORDER BY RPSS.name"""
    #
    #     select_query = select_query + group_by
    #
    #     request.env.cr.execute(select_query)
    #     order_lines = request.env.cr.dictfetchall()
    #
    #     records = []
    #
    #     if delivery_start_date != 'none' and delivery_end_date != 'none':
    #         for line in order_lines:
    #             if line['delivery_date'].date() >= self.string_to_date(delivery_start_date) and \
    #                     line['delivery_date'].date() <= self.string_to_date(delivery_end_date):
    #                 records.append([line['sale_order_id'],
    #                                 line['customer'], line['national_account'],
    #                                 line['delivery_date'],
    #                                 line['state'],
    #                                 line['total_amount']])
    #     else:
    #         for line in order_lines:
    #             records.append([line['sale_order_id'],
    #                             line['customer'], line['national_account'],
    #                             line['delivery_date'],
    #                             line['state'],
    #                             line['total_amount']])
    #
    #     res = request.make_response(
    #         self.from_data(["Sale Order#", "Customer Name", "National Account", "Delivery Date", "Status", "Total"],
    #                        records),
    #         headers=[('Content-Disposition', content_disposition('revenue_from_accounts_closed_in_12_months_by_na' + '.xls')),
    #                  ('Content-Type', 'application/vnd.ms-excel')],
    #     )
    #
    #     return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
