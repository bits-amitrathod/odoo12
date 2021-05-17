# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ExportNewAccountBonusReport(http.Controller):

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

    @http.route('/web/export/new_account_bonus_report_export/<string:start_date>/<string:end_date>/<string:business_development_id>/<string:key_account_id>',
                type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date, business_development_id, key_account_id, token=1, debug=1, **kw):

        select_query = """
                        SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                        so.name                             AS sale_order_id, 
                        rp.name                             AS customer, 
                        rpp.name                            AS business_development,
                        rppp.name                           AS key_account,
                        rps.name                            AS customer_business_development,
                        rpss.name                           AS customer_key_account,
                        ai.date_invoice                     AS date_invoice, 
                        CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                        CASE WHEN ai.state = 'open' then 'Open' 
                             WHEN ai.state = 'paid' then 'Paid' END AS invoice_state,
                        ai.amount_total                     AS amount_total, 
                        X.months                            AS months,
                        ai.currency_id                      AS currency_id,
                        X.first_occurence                   AS date_of_first_order
                FROM public.sale_order so
                INNER JOIN
                    (
                        SELECT sos.partner_id, MIN(aii.date_invoice) As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.date_invoice))) AS months    
                        FROM public.sale_order sos
                        INNER JOIN 
                            public.account_invoice aii ON sos.name = aii.origin
                        GROUP BY sos.partner_id
                        Having MIN(aii.date_invoice) > '""" + str(end_date) + """ ') X
                        ON so.partner_id = X.partner_id
                    INNER JOIN 
                        public.account_invoice ai ON so.name = ai.origin AND ai.state in ('open', 'paid')
                    INNER JOIN 
                        public.res_partner rp ON so.partner_id = rp.id
                    INNER JOIN 
                        public.res_users ru ON so.user_id = ru.id
                    INNER JOIN 
                        public.res_partner rpp ON ru.partner_id = rpp.id
                    LEFT OUTER JOIN 
                        public.res_users ruu ON so.account_manager = ruu.id
                    LEFT OUTER JOIN 
                        public.res_partner rppp ON ruu.partner_id = rppp.id
                    INNER JOIN
                        public.res_users rus ON rp.user_id = rus.id
                    INNER JOIN 
                        public.res_partner rps ON rus.partner_id = rps.id                        
                    LEFT OUTER JOIN 
                        public.res_users russ ON rp.account_manager_cust = russ.id
                    LEFT OUTER JOIN 
                        public.res_partner rpss ON russ.partner_id = rpss.id
                WHERE so.invoice_status = 'invoiced'                
                   """

        if business_development_id != "none":
            select_query = select_query + " AND rp.user_id = '" + str(business_development_id) + "'"

        if key_account_id != "none":
            select_query = select_query + " AND rp.account_manager_cust = '" + str(key_account_id) + "'"

        order_by = " ORDER BY rp.name"

        select_query = select_query + order_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([
                            line['customer'],
                            line['business_development'],
                            line['customer_business_development'],
                            line['key_account'],
                            line['customer_key_account'],
                            line['sale_order_id'],
                            line['date_invoice'],
                            line['amount_total'],
                            line['months'],
                            line['invoice_status'],
                            line['invoice_state']])

        res = request.make_response(
            self.from_data(["Customer Name", "#SO - Business Development", "Customer - Business Development", "#SO - Key Account", "Customer - Key Account", "Sale Order#", "Invoice Date", "Total",
                            "Months Ago First Order", "Invoice Status", "Status"],
                           records),
            headers=[('Content-Disposition', content_disposition('new_account_by_month_by_bd' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
