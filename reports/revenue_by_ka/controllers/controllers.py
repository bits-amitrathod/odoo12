# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
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

    @http.route('/web/export/revenue_by_ka_export/<string:start_date>/<string:end_date>/<string:key_account_id>', type='http',
                auth="public")
    @serialize_exception
    def download_document_xl(self, start_date, end_date, key_account_id, token=1, debug=1, **kw):

        select_query = """
                   SELECT
                       ROW_NUMBER () OVER (ORDER BY SP.id) AS id, 
                       SO.name                               AS sale_order_id,
                       SO.user_id                          AS salesperson,
                       SP.date_done                        AS delivery_date,
                       RP.name                             AS key_account,
                       ResPartner.name                     AS customer,
                       SO.account_manager                  AS key_account, 
                       PT.id                               AS product_tmpl_id,  
                       SO.amount_total                     AS total_amount 
                   FROM 
                       public.stock_picking SP

                   INNER JOIN 
                       public.sale_order SO 
                   ON 
                       (
                           SP.sale_id = SO.id)
                   INNER JOIN 
                       public.sale_order_line SOL 
                   ON 
                       (
                           SO.id = SOL.order_id)
                   INNER JOIN 
                       public.res_users RU 
                   ON 
                       (
                           SO.account_manager = RU.id)
                   INNER JOIN 
                       public.res_partner RP 
                   ON
                       ( 
                           RU.partner_id = RP.id)
                   INNER JOIN 
                       public.res_partner ResPartner 
                   ON
                       ( 
                           SO.partner_id = ResPartner.id)
                   INNER JOIN 
                       public.stock_move SM 
                   ON 
                       (
                           SP.id = SM.picking_id)
                   INNER JOIN 
                       public.stock_move_line SML
                   ON 
                       (
                           SM.id = SML.move_id)
                   INNER JOIN 
                       public.stock_production_lot SPL 
                   ON 
                       (
                           SML.lot_id = SPL.id)
                   INNER JOIN 
                       public.product_product PP 
                   ON 
                       (
                           SM.product_id = PP.id)
                   INNER JOIN 
                       public.product_template PT 
                   ON 
                       (
                           PP.product_tmpl_id = PT.id)

                   WHERE SO.state NOT IN ('cancel', 'void') AND SP.state = 'done' AND SP.picking_type_id = 5 
                       AND SM.product_id = SOL.product_id AND SO.account_manager IS NOT NULL

               """

        if start_date != "all" and end_date != "all":
            select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"

        if key_account_id != "none":
            select_query = select_query + "AND SO.account_manager = '" + str(key_account_id) + "'"

        group_by = """
                      GROUP BY
                      
                          SP.id, SO.name, SO.account_manager, SO.user_id, SO.amount_total, RP.name, ResPartner.name, PT.id
                          """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['sale_order_id'],
                            line['customer'], line['salesperson'], line['key_account'],
                            line['delivery_date'],
                            line['total_amount']])

        res = request.make_response(
            self.from_data(["Sale Order", "Customer", "Salesperson", "Key Account", "Delivery Date", "Total"],
                           records),
            headers=[('Content-Disposition', content_disposition('revenue_by_ka' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
