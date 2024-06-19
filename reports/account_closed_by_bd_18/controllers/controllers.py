# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
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

    @http.route('/web/export/account_closed_by_bd_export/<string:start_date>/<string:end_date>/<string:business_development_id>/'
                '<string:delivery_start_date>/<string:delivery_end_date>',
                type='http',
                auth="public")
    def download_document_xl(self, start_date, end_date, business_development_id, delivery_start_date,
                             delivery_end_date,
                             token=1, debug=1, **kw):

        select_query = """
                        SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                                so.id                               AS sale_order_id, 
                                so.partner_id                       AS customer, 
                                so.user_id                          AS business_development,
                                so.account_manager                  AS key_account,
                                so.state                            AS state,
                                MAX(SPS.date_done)                  AS delivery_date, 
                                rp.user_id                          AS customer_business_development,
                                rp.account_manager_cust             AS customer_key_account,
                                ai.invoice_date                     AS invoice_date, 
                                CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                                CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                                SUM(SOL.qty_delivered * SOL.price_reduce)                     AS total_amount, 
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
                            and aii.invoice_date > '""" + str(end_date) + """'
                        GROUP BY sos.partner_id
                        
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
                          "INTERVAL '1 year')  "

        if business_development_id:
            select_query = select_query + "AND so.user_id = '" + str(business_development_id) + "'"

        group_by = """ GROUP BY so.id, SPS.date_done, SOL.currency_id,rp.user_id, rp.account_manager_cust,
                      X.months  ,X.first_occurence ,ai.invoice_date,ai.state ,ai.currency_id  """

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
                                    line['customer'], line['business_development'],
                                    line['delivery_date'],
                                    line['state'],
                                    line['total_amount']])
        else:
            for line in order_lines:
                records.append([line['sale_order_id'],
                                line['customer'], line['business_development'],
                                line['delivery_date'],
                                line['state'],
                                line['total_amount']])

        res = request.make_response(
            self.from_data(["Sale Order#", "Customer Name", "Business Development", "Delivery Date", "Status", "Total"],
                           records),
            headers=[('Content-Disposition',
                      content_disposition('revenue_from_accounts_closed_in_12_months_by_bd' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res
    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
