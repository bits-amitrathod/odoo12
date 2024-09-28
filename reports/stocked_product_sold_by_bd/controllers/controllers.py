# -*- coding: utf-8 -*-
import datetime
import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class StockedProductSoldByBd(http.Controller):

    @staticmethod
    def from_data(field, rows):
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

    @http.route('/web/export/product_sold_by_bd_export/<string:start_date>/<string:end_date>/<string:business_development_id>',
                type='http',
                auth="public")
    def download_document_xl(self, start_date, end_date, business_development_id, token=1, debug=1, **kw):

        select_query = """
                    SELECT
                        ROW_NUMBER () OVER (ORDER BY SP.id) AS id, 
                        SO.name                             AS sale_order_id, 
                        SO.date_order                       AS date_order,
                        SO.user_id                  AS business_development_id,
                        SP.date_done                        AS delivery_date,
                        RP.name                             AS business_development,
                        ResPartner.name                     AS customer_id,
                        SO.state                            AS status,
                        PT.name                             AS product_tmpl_id, 
                        PT.sku_code                         AS sku_code, 
                        SOL.price_reduce                    AS unit_price, 
                        UU.name                             AS product_uom_id,                        
                        SOL.currency_id                     AS currency_id,

                        CASE WHEN (SELECT SUM(SMLS.qty_done)
                        FROM public.stock_picking SPS
                        INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                        INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                        INNER JOIN public.stock_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                        WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7) is null THEN SUM(SML.qty_done) ELSE
                        (SUM(SML.qty_done) - (SELECT SUM(SMLS.qty_done)
                        FROM public.stock_picking SPS
                        INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                        INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                        INNER JOIN public.stock_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                        WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7)) END AS qty_done,


                        CASE WHEN (SELECT SUM(SMLS.qty_done)
                        FROM public.stock_picking SPS
                        INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                        INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                        INNER JOIN public.stock_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                        WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7) is null THEN SUM(SML.qty_done) ELSE
                        (SUM(SML.qty_done) - (SELECT SUM(SMLS.qty_done)
                        FROM public.stock_picking SPS
                        INNER JOIN public.stock_move SMS ON SPS.id = SMS.picking_id
                        INNER JOIN public.stock_move_line SMLS ON SMS.id = SMLS.move_id AND SMS.product_id = SM.product_id
                        INNER JOIN public.stock_lot SPLS ON SMLS.lot_id = SPLS.id AND SPLS.use_date <= SP.date_done + INTERVAL '6 MONTH'
                        WHERE SPS.sale_id = SO.id AND SPS.state = 'done' AND SPS.picking_type_id = 7)) END * SOL.price_reduce AS total_amount


                    FROM 
                        public.sale_order SO 

                    INNER JOIN 
                        public.sale_order_line SOL 
                    ON 
                        (
                            SO.id = SOL.order_id)
                    INNER JOIN 
                        public.stock_picking SP 
                    ON 
                        (
                            SO.id = SP.sale_id AND SP.state = 'done' AND SP.picking_type_id = 5)
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
                            SO.partner_id = ResPartner.id)
                    INNER JOIN 
                        public.stock_move SM 
                    ON 
                        (
                            SP.id = SM.picking_id AND SM.product_id = SOL.product_id)
                    INNER JOIN 
                        public.stock_move_line SML
                    ON 
                        (
                            SM.id = SML.move_id)
                    INNER JOIN 
                        public.stock_lot SPL 
                    ON 
                        (
                            SML.lot_id = SPL.id AND SPL.use_date <= SP.date_done + INTERVAL '6 MONTH')
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
                    INNER JOIN
                        public.uom_uom UU
                    ON
                        (
                            PT.uom_id = UU.id)

                    WHERE SO.state NOT IN ('cancel', 'void') AND SO.user_id IS NOT NULL AND SO.account_manager IS NULL

                """

        if start_date != "all" and end_date != "all":
            select_query = select_query + " AND SP.date_done BETWEEN '" + str(
                start_date) + "'" + " AND '" + str(self.string_to_date(end_date) + datetime.timedelta(days=1)) + "'"

        if business_development_id != "none":
            select_query = select_query + "AND SO.user_id = '" + str(business_development_id) + "'"

        group_by = """
                            GROUP BY
                                SM.product_id, SO.id, SP.date_done, PT.id, SOL.price_reduce, SOL.currency_id, SP.id, 
                                RP.name, ResPartner.name, UU.name 
                                ORDER BY RP.name  
                                """

        select_query = select_query + group_by

        request.env.cr.execute(select_query)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['sku_code'], line['product_tmpl_id'], line['customer_id'], line['sale_order_id'],
                            line['business_development'],
                            line['delivery_date'],
                            line['status'],
                            line['qty_done'], line['product_uom_id'], line['unit_price'], line['total_amount']])

        res = request.make_response(
            self.from_data(
                ["Product SKU", "Product Name", "Customer Name", "Sale Order#", "Business Development ", "Delivery Date",
                 "Status", "Delivered Quantity", "Product UOM", "Unit Price", "Total"],
                records),
            headers=[
                ('Content-Disposition', content_disposition('short_date_and_over_stocked_product_sold_by_bd' + '.xls')),
                ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()
