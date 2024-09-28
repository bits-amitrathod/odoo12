# -*- coding: utf-8 -*-
import datetime

import math
from odoo import http, _, fields
from odoo.addons.web.controllers.main import content_disposition
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import pycompat, io, re, xlwt


class ReportPrintSalesPurchaseHistory(http.Controller):

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

    @http.route('/web/export/sale_purchase_history_export/<string:start_date>/<string:end_date>', type='http', auth="public")
    def download_document_xl(self, start_date, end_date, token=1, debug=1, **kw):

        str_functions_old = """	 

           select pp.default_code as sku,rp.name cust_name,so.name so,pt.name prod_name,sp.date_done,
                    round( sol.qty_delivered, 2) as qty ,um.name as uom,
                    round( sol.price_unit, 2) as price_unit ,round((sol.qty_delivered * sol.price_unit),2) as total,
                    CASE   WHEN quotations_per_code.quotation_count IS NULL THEN '0' 
                                     ELSE quotations_per_code.quotation_count
                                   END     AS quotation_count,
                     (select resa.name from res_users rus join res_partner rps on rus.id=rps.account_manager_cust 
			left join res_partner resa on rus.partner_id = resa.id
			where rus.id=rp.account_manager_cust limit 1 ) as account_mang
                    from sale_order_line  sol 
                    left join sale_order so on sol.order_id = so.id 

                    left join product_product pp on sol.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id
                    left join res_partner rp on so.partner_id = rp.id
                    left join stock_picking sp on sp.sale_id=so.id 

                    left join uom_uom um on um.id = sol.product_uom

                    left join (SELECT ppc.id,count(ppc.id) as quotation_count 
                                            from  product_product ppc   
                                               INNER JOIN sale_order_line soli ON soli.product_id=ppc.id 
                                               INNER JOIN product_template pti ON  pti.id=ppc.product_tmpl_id 
                                               INNER JOIN sale_order sor ON sor.id=soli.order_id   
                                                where sor.state in ('draft','sent')   
                                                   GROUP  BY ppc.id) AS quotations_per_code
                                                   on pp.id =  quotations_per_code.id  

                    where so.state not in ('cancel','void') and sol.price_unit >= 0 and sp.state ='done' 
                    and sp.location_dest_id in  (select id from stock_location where name='Customers' and active =true
                     order by id desc )   and sol.qty_delivered > 0 and pp.active =true and pt.active =true

        """

        str_functions = """	 

                    select pp.default_code as sku,rp.name cust_name,so.name so,pt.name prod_name,sp.date_done,
                    round( sol.qty_delivered, 2) as qty ,um.name as uom,
                    round( sol.price_unit, 2) as price_unit ,round((sol.qty_delivered * sol.price_unit),2) as total,
                    CASE   WHEN quotations_per_code.quotation_count IS NULL THEN '0' 
                                     ELSE quotations_per_code.quotation_count
                                   END     AS quotation_count,

				rp.is_share,rp.is_broker,rp.sale_margine as sale_level,cr.name as sales_team,
				account_mang.name as account_mang,sales_person.name as sales_person
                    from sale_order_line  sol 
                    left join sale_order so on sol.order_id = so.id 

                    left join product_product pp on sol.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id
                    left join res_partner rp on so.partner_id = rp.id
                    left join stock_picking sp on sp.sale_id=so.id 

                    left join uom_uom um on um.id = sol.product_uom
					left join crm_team cr on cr.id = so.team_id

					left join (select rps2.name,rps.id from res_users rus join res_partner rps on rus.id=rps.account_manager_cust 
					right join res_partner rps2 on rps2.id = rus.partner_id 
					where rps.active=true and rus.active=true) as account_mang on  account_mang.id=rp.id

				    left join (select rps2.name,rps.id from res_users rus join res_partner rps on rus.id=rps.user_id 
					right join res_partner rps2 on rps2.id = rus.partner_id 
					where rps.active=true and rus.active=true) as sales_person on  sales_person.id=rp.id

                    left join (SELECT ppc.id,count(ppc.id) as quotation_count 
                                            from  product_product ppc   
                                               INNER JOIN sale_order_line soli ON soli.product_id=ppc.id 
                                               INNER JOIN product_template pti ON  pti.id=ppc.product_tmpl_id 
                                               INNER JOIN sale_order sor ON sor.id=soli.order_id   
                                                where sor.state in ('draft','sent')   
                                                   GROUP  BY ppc.id) AS quotations_per_code
                                                   on pp.id =  quotations_per_code.id  

                    where so.state not in ('cancel','void') and sol.price_unit >= 0 and sp.state ='done' 
                    and sp.location_dest_id in  (select id from stock_location where name='Customers' and active =true
                     order by id desc )   and sol.qty_delivered > 0 and pp.active =true and pt.active =true

                """

        if start_date != "all" and end_date != "all":
            str_functions = str_functions + """ and sp.date_done >= '""" + str(
                start_date) + """' and sp.date_done <= '""" + \
                            str(end_date) + """' """

        request.env.cr.execute(str_functions)
        order_lines = request.env.cr.dictfetchall()

        records = []

        for line in order_lines:
            records.append([line['sku'], line['cust_name'], line['sales_person'], line['account_mang'], line['so'],
                            line['prod_name'],
                            line['is_broker'], line['is_share'], line['sales_team'], line['sale_level'],
                            line['date_done'], line['qty'], line['uom'], line['price_unit'],
                            line['total'], line['quotation_count']])

        res = request.make_response(
            self.from_data(["Product SKU", "Customer Name", "Business Development", "Key Account ", "Sales Order#",
                            "Product Name", "Is Broker", "Is Shared", "Sales Team", "Sales Level",
                            "Delivered Date"
                               , "Delivered Qty", "UOM", "Unit Price", "Total", "Open Quotations Per Code"],
                           records),
            headers=[('Content-Disposition', content_disposition('payroll_report' + '.xls')),
                     ('Content-Type', 'application/vnd.ms-excel')],
        )

        return res
