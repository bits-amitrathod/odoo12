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

from odoo import api, fields, models
from odoo.tools import float_repr
import datetime
import logging

class salebymonth():
    product_name = ''
    current_month_total_qty = 0
    current_month_total_amount = 0
    last_month_total_qty = 0
    last_month_total_amount = 0
    sku=''

    @api.multi
    def addObject(self, filtered_by_current_month):
        dict = {}
        for record in filtered_by_current_month:
            for r1 in record.order_line:
                if r1.product_id.id in dict:
                    # log.info(" current_month Key available in dictionary")
                    data = dict[r1.product_id.id]
                    data.current_month_total_qty = data.current_month_total_qty + r1.product_uom_qty
                    data.current_month_total_amount = data.current_month_total_amount + r1.price_subtotal
                    dict[r1.product_id.id] = data
                else:
                    # log.info(" current_month not Key available in dictionary")
                    object = salebymonth()
                    object.current_month_total_qty = r1.product_uom_qty
                    object.current_month_total_amount = r1.price_subtotal
                    object.product_name = r1.product_id.name
                    object.sku = r1.product_id.product_tmpl_id.sku_code
                    dict[r1.product_id.id] = object

        return dict

class SaleSalespersonReport(models.TransientModel):
    _name = 'sale.productbymonth.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products")

    @api.model
    def check(self, data):
        if data:
            return data
        else:
            return " "

    @api.multi
    def print_salesbymonth_vise_report(self):
        sale_orders = self.env['sale.order'].search([])
        groupby_dict = {}
        # for user in self.product_id:
            # filtered_order = list(filter(lambda x: x.product_id == user, sale_orders))
        filtered_by_date = list(
                filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, sale_orders))
        groupby_dict = salebymonth().addObject(filtered_by_date)

        final_dict = {}
        temp = []
        for user in groupby_dict.keys():
            order =groupby_dict[user]
            temp_2 = []
            temp_2.append(order.sku)
            temp_2.append(order.product_name)
            temp_2.append(float_repr(order.current_month_total_amount,precision_digits=2))
            temp_2.append(int(order.current_month_total_qty))
            temp.append(temp_2)
        final_dict['data'] = temp
        final_dict['data'].sort(key=lambda x: self.check(x[0]))
        datas = {
            'ids': self,
            'model': 'sale.product.report',
            'form': final_dict,
            'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
            'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),

        }
        action = self.env.ref('sr_sales_report_product_bymonth.action_report_sales_salesbymonth_wise').report_action([],
                                                                                                                    data=datas)
        action.update({'target': 'main'})
        return action

