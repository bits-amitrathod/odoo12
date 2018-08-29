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
from numpy.core.defchararray import upper
import datetime
import logging

log = logging.getLogger(__name__)

class comparebymonth():
    sale_order =''
    customer =''
    confirmation_date = 0
    amount = 0
    discount_amount = 0
    total_amount = 0

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "

    @api.multi
    def addObject(self, filtered_by_current_month):
        dict = {}
        log.info(" inside addObject ")
        for record in filtered_by_current_month:
            object = comparebymonth()
            object.sale_order = record.name
            object.customer = record.partner_id.name
            if record.confirmation_date:
                object.confirmation_date = datetime.datetime.strptime(record.confirmation_date, "%Y-%m-%d %H:%M:%S").date().strftime('%m/%d/%Y')
            else:
                object.confirmation_date = record.confirmation_date
            sum=0
            for r1 in record.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)

            object.amount = record.amount_untaxed
            object.discount_amount = float(round(sum -record.amount_untaxed))
            object.total_amount = record.amount_total
            dict[record.id] = object

        log.info(" return addObject ")
        return dict

class DiscountSummaryReport(models.TransientModel):
    _name = 'sale.discount.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products")

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "

    @api.multi
    def print_discountsummary_vise_report(self):
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        groupby_dict = {}
        filtered_by_current_month = sale_orders
        dat = comparebymonth().addObject(filtered_by_current_month)
        final_list = []
        for user in dat.keys():
            order = dat[user]
            temp_2 = []
            temp_2.append(order.sale_order)
            temp_2.append(order.customer)
            temp_2.append(order.confirmation_date)
            temp_2.append(float_repr(order.amount,precision_digits=2))
            temp_2.append(float_repr(order.discount_amount,precision_digits=2))
            temp_2.append(float_repr(order.total_amount,precision_digits=2))
            final_list.append(temp_2)
        final_list.sort(key=lambda x:self.check(str(x[0])))
        # final_dict['data'].sort(key=lambda x: x[0])
        datas = {
            'ids': self.ids,
            'model': self._module,
            'form': final_list,
        }
        log.info('............bbb..................')
        return self.env.ref('sales_report_discount_summary.action_report_sales_discount_summary_wise').report_action([],
                                                                                                                    data=datas)
