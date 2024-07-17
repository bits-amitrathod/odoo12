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
import logging

_logger = logging.getLogger(__name__)
class ReportSaleOrderLineGroupByProduct(models.AbstractModel):
    _name = 'report.report_sale_orders_groupby_product.group_by_product'
    _description = "Report Sale Order Line Group By Product"

    @api.model
    def _get_report_values(self, docids, data=None):

        sale_order_lines =self.env['sale.order.line'].browse(docids)
        _logger.info("sale line: %r",sale_order_lines)
        self.env.cr.execute("""
                     SELECT
                           distinct sale_order_line.product_id,
                           product_template.name,
                           array_agg(ARRAY[
                                   sale_order.name,
                                   to_char(sale_order.date_order,'MM/DD/YYYY'),
                                   product_template.sku_code,
                                   CAST (concat(cast(round(sale_order_line.qty_delivered) as text),'  ',uom_uom.name) as text),
                                   CAST (sale_order_line.price_subtotal as text),
                                   CAST (sale_order_line.currency_id as text)
                            ]) as table
            FROM
               public.stock_move
            LEFT OUTER JOIN public.sale_order_line
            ON ( public.stock_move.sale_line_id = public.sale_order_line.id)
            INNER JOIN public.product_product
            ON ( public.sale_order_line.product_id = public.product_product.id)
            INNER JOIN public.sale_order
            ON ( public.sale_order_line.order_id = public.sale_order.id)
            INNER JOIN public.product_template
            ON ( public.product_product.product_tmpl_id = public.product_template.id)
            RIGHT OUTER JOIN public.uom_uom
            ON ( public.product_template.uom_id = public.uom_uom.id)
            WHERE public.sale_order_line.product_id = public.product_product.id
            AND public.sale_order.id = public.sale_order_line.order_id
            AND public.product_product.product_tmpl_id = public.product_template.id
            AND  public.stock_move.location_id = 16
            AND public.stock_move.state like 'done'
            AND public.sale_order_line.id IN (""" + ",".join(
                        map(str, docids)) + """)
             Group BY product_template.name,sale_order_line.product_id
             Order BY product_template.name desc   """)

        result = self.env.cr.dictfetchall()
        popup = self.env['popup.sale.orders.groupby.product.report'].search([('create_uid', '=', self._uid)], limit=1,
                                                                            order="id desc")
        return {
            'data': result,
            'popup': popup
        }