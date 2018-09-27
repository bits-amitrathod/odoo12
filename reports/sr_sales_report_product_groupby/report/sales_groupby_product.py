# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from odoo import api, models


class ReportSaleOrderLineGroupByProduct(models.AbstractModel):
    _name = 'report.sr_sales_report_product_groupby.group_by_product'

    @api.model
    def get_report_values(self, docids, data=None):
        self.env.cr.execute("""
                   SELECT 
                      distinct sale_order_line.product_id,
                      product_template.name,
                      array_agg(ARRAY[sale_order.name,to_char(sale_order.date_order,'MM/DD/YYYY'),CAST (sale_order.amount_total as text),CAST (sale_order_line.currency_id as text)]) as table
                    FROM 
                      public.sale_order_line, 
                      public.sale_order, 
                      public.product_product, 
                      public.product_template
                    WHERE 
                      sale_order_line.product_id = product_product.id AND
                      sale_order.id = sale_order_line.order_id AND
                      product_product.product_tmpl_id = product_template.id and sale_order_line.id in ("""+",".join(map(str, docids))+""")
                    Group BY
                      product_template.name,sale_order_line.product_id
                    Order BY
                      product_template.name desc
                  """)

        result = self.env.cr.dictfetchall()

        return {
            'data': result
        }
