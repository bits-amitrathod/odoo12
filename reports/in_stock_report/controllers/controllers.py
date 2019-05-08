# -*- coding: utf-8 -*-
import datetime

import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt


class ReportPrintInStockExport(http.Controller):

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
                if i == 3:
                    worksheet.col(i).width = 20000  #
                else:
                    worksheet.col(i).width = 4000  # around 110 pixels

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

    @http.route('/web/export/in_stock_report', type='http', auth="public")
    @serialize_exception
    def download_document_xl(self,token, **kwargs):

        str_query = """
        
        SELECT
            CONCAT(sale_order.partner_id, product_product.id) as id,
            public.res_partner.name as res_partner,
            sale_order.partner_id,
            public.product_brand.name as product_brand,
            public.product_template.sku_code,
            public.product_template.name as product_template,
            public.product_uom.name as product_uom,
            public.sale_order_line.product_id,
            sale_order.partner_id
        FROM
            public.sale_order
        INNER JOIN
            public.sale_order_line
        ON
            (
                public.sale_order.id = public.sale_order_line.order_id)
        INNER JOIN
            public.product_product
        ON
            (
                public.sale_order_line.product_id = public.product_product.id)
        INNER JOIN
            public.product_template
        ON
            (
                public.product_product.product_tmpl_id = public.product_template.id)
        INNER JOIN
            public.res_partner
        ON
            (
                public.sale_order.partner_id = public.res_partner.id)
        INNER JOIN
            public.product_brand
        ON
            (
                public.product_template.product_brand_id = public.product_brand.id)
        INNER JOIN
            public.product_uom
        ON
            (
                public.product_template.uom_id = public.product_uom.id)
        
        """

        request.env.cr.execute(str_query)
        order_lines = request.env.cr.dictfetchall()

        data = {}
        print("-------------1------------")
        print(len(order_lines))
        count = 0
        for line in order_lines:
            if not line['id'] in data:
                product = request.env['product.product'].browse(line['product_id'])
                qty = product.product_tmpl_id.actual_quantity
                if not qty:
                    continue

                partner = request.env['res.partner'].browse(line['partner_id'])
                if partner.property_product_pricelist.id:
                    price_list = partner.property_product_pricelist.get_product_price(product, 1.0, partner)
                else:
                    price_list = product.product_tmpl_id.list_price

                line['price_list'] = price_list
                line['actual_quantity'] = qty

                request.env.cr.execute(
                    """
                    SELECT 
                        min(use_date), max(use_date)
                    FROM
                        stock_quant
                    INNER JOIN
                        stock_production_lot
                    ON
                        (
                            stock_quant.lot_id = stock_production_lot.id)
                    INNER JOIN
                        stock_location
                    ON
                        (
                            stock_quant.location_id = stock_location.id)
                    WHERE
                        stock_location.usage in('internal', 'transit') and stock_production_lot.product_id  = %s
                        """,

                    (line['product_id'],))
                query_result = request.env.cr.dictfetchone()
                if query_result['min']:
                    line['min_expiration_date'] = fields.Date.from_string(query_result['min']).strftime('%m/%d/%Y')
                else:
                    line['min_expiration_date'] = "N/A"
                if query_result['max']:
                    line['max_expiration_date'] = fields.Date.from_string(query_result['max']).strftime('%m/%d/%Y')
                else:
                    line['max_expiration_date'] = "N/A"

                data[line['id']] = line
            count = count + 1
            print("-------------" + str(count) + "------------")

        print("-------------2------------")
        records = []

        for line in data.values():
            records.append([line['res_partner'], line['product_brand'], line['sku_code'], line['product_template'],
                            "$" + str(line['price_list']), line['actual_quantity'], line['product_uom'],
                            line['min_expiration_date'], line['max_expiration_date']])

        res = request.make_response(
            self.from_data(["partner_name", "brand_name", "sku_code", "product_name", "price_list"
                               , "actual_quantity", "product_uom","min_expiration_date", "max_expiration_date"], records),
            headers=[('Content-Disposition', content_disposition('in_stock_report' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )
        res.set_cookie('fileToken', token)


        return res
