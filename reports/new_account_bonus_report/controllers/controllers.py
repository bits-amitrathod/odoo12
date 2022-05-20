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
                if i == 0:
                    worksheet.col(i).width = 10000  #
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

    @http.route('/web/export/new_account_bonus_report_export/<string:start_date>/<string:end_date>/<string:end_date_13>/<string:end_date_13_12months>/<string:business_development_id>/<string:key_account_id>',
                type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date,end_date_13,end_date_13_12months,
                             business_development_id, key_account_id, token=1, debug=1, **kw):

        # select_query = """
        #                 SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id,
        #                 so.name                             AS sale_order_id,
        #                 rp.name                             AS customer,
        #                 rpp.name                            AS business_development,
        #                 rppp.name                           AS key_account,
        #                 rps.name                            AS customer_business_development,
        #                 rpss.name                           AS customer_key_account,
        #                 ai.invoice_date                     AS invoice_date,
        #                 CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
        #                 CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
        #                   SUM(SOL.qty_delivered * SOL.price_reduce)                      AS amount_total,
        #                 X.months                            AS months,
        #                 ai.currency_id                      AS currency_id,
        #                 X.first_occurence                   AS date_of_first_order
        #         FROM public.sale_order so
        #         INNER JOIN
        #             (
        #             (SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
        #                     DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months
        #                 FROM public.sale_order sos
        #                 INNER JOIN
        #                     public.account_move aii ON sos.name = aii.invoice_origin
        #                 GROUP BY sos.partner_id
        #                 Having MIN(aii.invoice_date) > '""" + str(end_date) + """ ')
        #
        #                 UNION
        #
        #                 ( SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
        #                     DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months
        #                 FROM public.sale_order sos
        #                 INNER JOIN public.res_partner rep ON sos.partner_id= rep.id
        #                 INNER JOIN public.account_move aii ON sos.name = aii.invoice_origin
        #                 where rep.reinstated_date > ' """ + str(end_date) + """ ' and rep.reinstated_date is not null
        #
        #                 and  aii.invoice_date > ' """ + str(end_date) + """ '  GROUP BY sos.partner_id )
        #
        #             ) X
        #                 ON so.partner_id = X.partner_id
        #             INNER JOIN
        #                 public.account_move ai ON so.name = ai.invoice_origin AND ai.state in ('posted')
        #             INNER JOIN
        #                 public.res_partner rp ON so.partner_id = rp.id
        #             INNER JOIN
        #                 public.res_users ru ON so.user_id = ru.id
        #             INNER JOIN
        #                 public.res_partner rpp ON ru.partner_id = rpp.id
        #             LEFT OUTER JOIN
        #                 public.res_users ruu ON so.account_manager = ruu.id
        #             LEFT OUTER JOIN
        #                 public.res_partner rppp ON ruu.partner_id = rppp.id
        #             INNER JOIN
        #                 public.res_users rus ON rp.user_id = rus.id
        #             INNER JOIN
        #                 public.res_partner rps ON rus.partner_id = rps.id
        #             LEFT OUTER JOIN
        #                 public.res_users russ ON rp.account_manager_cust = russ.id
        #             LEFT OUTER JOIN
        #                 public.res_partner rpss ON russ.partner_id = rpss.id
        #             INNER JOIN public.sale_order_line SOL ON so.id = SOL.order_id
        #             INNER JOIN
        #             (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5
        #             AND state = 'done' ORDER BY origin) AS SPS
        #             ON so.id = SPS.sale_id
        #             INNER JOIN  public.product_product  pp on SOL.product_id = pp.id
        #             INNER JOIN  public.product_template  pt on pp.product_tmpl_id = pt.id and pt.type!='service'
        #         WHERE so.invoice_status = 'invoiced'
        #            """
        #
        # if business_development_id != "none":
        #     select_query = select_query + " AND rp.user_id = '" + str(business_development_id) + "'"
        #
        # if key_account_id != "none":
        #     select_query = select_query + " AND rp.account_manager_cust = '" + str(key_account_id) + "'"
        #
        # group_by = """ GROUP BY so.id,rp.name, rpp.name, rppp.name ,rps.name  ,rpss.name
        # ,rp.user_id,
        #  X.months  ,X.first_occurence ,ai.invoice_date,ai.state,ai.currency_id  """
        #
        # select_query = select_query + group_by
        #
        # order_by = " ORDER BY rp.name"
        #
        # select_query = select_query + order_by

        select_query = """
                       SELECT ROW_NUMBER () OVER (ORDER BY sale_order_id)  AS id,sale_order_id,customer,customer_name,
                       sale_order_name,business_development_name,key_account_name,customer_business_development_name,
                       customer_key_account_name,
                       business_development,key_account
                      ,customer_business_development,customer_key_account,invoice_date,invoice_status,invoice_state,amount_total
                      ,amount_total_thirteen
                      ,months,currency_id,date_of_first_order from
                      (  (
                        SELECT 
                                so.id                               AS sale_order_id, 
                                so.partner_id                       AS customer, 
                                rp.name                             AS customer_name,
                                so.name                       AS sale_order_name, 
                                so.user_id                          AS business_development,
                                so.account_manager                  AS key_account,
                                rp.user_id                          AS customer_business_development,
                                rp.account_manager_cust             AS customer_key_account,
                                
                                rpp.name                            AS business_development_name,
                                rppp.name                           AS key_account_name,
                                rps.name                            AS customer_business_development_name,
                                rpss.name                           AS customer_key_account_name,
                                
                                ai.invoice_date                     AS invoice_date, 
                                CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                                CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                                SUM(SOL.qty_delivered * SOL.price_reduce)                     AS amount_total, 
                                0 as amount_total_thirteen,
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
                                
                            INNER JOIN public.sale_order_line SOL ON so.id = SOL.order_id 
                            INNER JOIN 
                            (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 
                            AND state = 'done' ORDER BY origin) AS SPS 
                            ON so.id = SPS.sale_id
                            INNER JOIN  public.product_product  pp on SOL.product_id = pp.id 
                            INNER JOIN  public.product_template  pt on pp.product_tmpl_id = pt.id and pt.type!='service'
                        WHERE so.invoice_status = 'invoiced'       and ai.invoice_date >= ' """ + str(end_date) + """ ' 

                           """

        if business_development_id != "none":
            select_query = select_query + " AND rp.user_id = '" + str(business_development_id) + "'"

        if key_account_id != "none":
            select_query = select_query + " AND rp.account_manager_cust = '" + str(key_account_id) + "'"

        group_by = """ GROUP BY so.id, so.partner_id,so.user_id,rp.user_id,rp.name , so.account_manager ,rp.account_manager_cust,
        so.name ,rpp.name,rppp.name,rps.name,rpss.name,
                                 X.months  ,X.first_occurence ,ai.invoice_date,ai.state,ai.currency_id  """

        select_query = select_query + group_by

        order_by = " ORDER BY ai.invoice_date asc )"

        cust_without_sale_order = """           
                                   UNION
                    				 (
                    						SELECT 
                                so.id                               AS sale_order_id, 
                                so.partner_id                       AS customer, 
                                rp.name                             AS customer_name,
                                so.name                       AS sale_order_name, 
                                so.user_id                          AS business_development,
                                so.account_manager                  AS key_account,
                                rp.user_id                          AS customer_business_development,
                                rp.account_manager_cust             AS customer_key_account,
                                
                                rpp.name                            AS business_development_name,
                                rppp.name                           AS key_account_name,
                                rps.name                            AS customer_business_development_name,
                                rpss.name                           AS customer_key_account_name,
                                
                                ai.invoice_date                     AS invoice_date, 
                                CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                                CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                                0                     AS amount_total, 
                                SUM(SOL.qty_delivered * SOL.price_reduce)    as amount_total_thirteen,
                                DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(ai.invoice_date))) AS months ,
                                ai.currency_id                      AS currency_id,
                                X.first_occurence                   AS date_of_first_order
                        FROM public.sale_order so
                        INNER JOIN
                            (
                            (SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                                    DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                                FROM public.sale_order sos
                                   INNER JOIN public.res_partner rep ON sos.partner_id= rep.id 
                                INNER JOIN 
                                    public.account_move aii ON sos.name = aii.invoice_origin
                                where rep.reinstated_date is  null
                                GROUP BY sos.partner_id
                                Having MIN(aii.invoice_date) > '""" + str(end_date_13) + """ '  and 
                                 MIN(aii.invoice_date) < '""" + str(end_date) + """ ' )


                                UNION

                                ( SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                                    DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                                FROM public.sale_order sos 
                                INNER JOIN public.res_partner rep ON sos.partner_id= rep.id 
                                INNER JOIN public.account_move aii ON sos.name = aii.invoice_origin 
                                where rep.reinstated_date > ' """ + str(end_date_13) + """ ' and rep.reinstated_date is not null
                               and rep.reinstated_date < ' """ + str(end_date) + """ '
                                and  aii.invoice_date > ' """ + str(end_date_13) + """ ' 
                                  and aii.invoice_date < ' """ + str(end_date) + """ ' GROUP BY sos.partner_id )

                            ) X
                                ON so.partner_id = X.partner_id
                            INNER JOIN 
                                public.account_move ai ON so.name = ai.invoice_origin AND ai.state in ('posted') 

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
                                
                                INNER JOIN public.sale_order_line SOL ON so.id = SOL.order_id 
                            INNER JOIN 
                            (SELECT DISTINCT ON (origin) origin,date_done,sale_id  FROM stock_picking WHERE picking_type_id = 5 
                            AND state = 'done' ORDER BY origin) AS SPS 
                            ON so.id = SPS.sale_id
                            INNER JOIN  public.product_product  pp on SOL.product_id = pp.id 
                            INNER JOIN  public.product_template  pt on pp.product_tmpl_id = pt.id and pt.type!='service'
                        WHERE so.invoice_status = 'invoiced' and   (    ai.invoice_date >= ' """ + str(end_date_13) + """ ' 
                         and ai.invoice_date <  ' """ + str(end_date_13_12months) + """ ' )


                                    """

        if business_development_id != "none":
            cust_without_sale_order = cust_without_sale_order + " AND rp.user_id = '" + str(
                business_development_id) + "'"

        if key_account_id != "none":
            cust_without_sale_order = cust_without_sale_order + " AND rp.account_manager_cust = '" + str(
                key_account_id) + "'"

        # group_by_sale = """ GROUP BY so.id, so.partner_id,so.user_id,rp.user_id, so.account_manager ,rp.account_manager_cust,
        #              ai.invoice_date,ai.state,ai.currency_id   )) as testbonus """

        group_by_sale = """ GROUP BY so.id, so.partner_id,so.user_id,rp.user_id,rp.name , so.account_manager ,rp.account_manager_cust,
        so.name ,rpp.name,rppp.name,rps.name,rpss.name,
                                             X.months  ,X.first_occurence ,ai.invoice_date,ai.state,ai.currency_id  )) as testbonus """

        select_query = select_query + order_by + cust_without_sale_order + group_by_sale

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([
                            line['customer_name'],
                            line['business_development_name'],
                            line['customer_business_development_name'],
                            line['key_account_name'],
                            line['customer_key_account_name'],
                            line['sale_order_name'],
                            line['invoice_date'],
                            line['amount_total'],
                            line['amount_total_thirteen'],
                            line['months'],
                            line['invoice_status'],
                            line['invoice_state']])

        res = request.make_response(
            self.from_data(["Customer Name", "#SO - Business Development", "Customer - Business Development", "#SO - Key Account", "Customer - Key Account", "Sale Order#", "Invoice Date", "Total","All Total",
                            "Months Ago First Order", "Invoice Status", "Status"],
                           records),
            headers=[('Content-Disposition', content_disposition('new_account_by_month_by_bd' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
