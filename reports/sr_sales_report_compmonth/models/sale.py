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
import operator

from odoo.fields import Field
from numpy.core.defchararray import upper
log = logging.getLogger(__name__)

class comparebymonth():
    product_name = ''
    current_month_total_qty = 0
    current_month_total_amount = 0
    last_month_total_qty = 0
    last_month_total_amount = 0
    sku=''

    @api.multi
    def addObject(self, filtered_by_current_month, filtered_by_last_month):
        dict = {}
        log.info(" inside addObject ")
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
                    object = comparebymonth()
                    object.current_month_total_qty = r1.product_uom_qty
                    object.current_month_total_amount = r1.price_subtotal
                    object.product_name = r1.product_id.name
                    object.sku = r1.product_id.product_tmpl_id.sku_code
                    dict[r1.product_id.id] = object

        for record in filtered_by_last_month:
            for r1 in record.order_line:
                if r1.product_id.id in dict:
                    # log.info(" last_month Key available in dictionary")
                    data = dict[r1.product_id.id]
                    data.last_month_total_qty = data.last_month_total_qty + r1.product_uom_qty
                    data.last_month_total_amount = data.last_month_total_amount + r1.price_subtotal
                    dict[r1.product_id.id] = data
                else:
                    # log.info(" last_month Key not available in dictionary")
                    object = comparebymonth()
                    object.last_month_total_qty = r1.product_uom_qty
                    object.last_month_total_amount = r1.price_subtotal
                    object.product_name = r1.product_id.name
                    object.sku = r1.product_id.product_tmpl_id.sku_code
                    dict[r1.product_id.id] = object
        log.info(" return addObject ")
        return dict

class SaleSalespersonReport(models.TransientModel):
    _name = 'sale.compbymonth.report'

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "
    @api.multi
    def print_compbymonth_vise_report(self):
        sale_orders = self.env['sale.order'].search([])
        groupby_dict = {}

        s_date = (fields.date.today()-datetime.timedelta(days=30))
        l_date = (fields.date.today())
        filtered_by_current_month = list(filter(lambda x:fields.Datetime.from_string(x.date_order).date() >= s_date and fields.Datetime.from_string(x.date_order).date() <= l_date ,sale_orders))

        ps_date = (fields.date.today() - datetime.timedelta(days=60))
        pl_date = (fields.date.today() - datetime.timedelta(days=31))
        filtered_by_last_month = list(filter(lambda x: fields.Datetime.from_string(x.date_order).date() >= ps_date and fields.Datetime.from_string(x.date_order).date() <= pl_date ,sale_orders))
        dat = comparebymonth().addObject(filtered_by_current_month,filtered_by_last_month)
        groupby_dict['data'] = dat
        final_list = []
        for user in dat.keys():
            order= dat[user]
            temp_2 = []
            temp_2.append(order.product_name)
            temp_2.append(int(order.current_month_total_qty))
            temp_2.append(float_repr(order.current_month_total_amount,precision_digits=2))
            temp_2.append(int(order.last_month_total_qty))
            temp_2.append(float_repr(order.last_month_total_amount,precision_digits=2))
            temp_2.append(order.sku)
            final_list.append(temp_2)
        final_list.sort(key=lambda x: self.check(str(x[5])))

        datas = {
            'ids': self.ids,
            'model': self._module,
            'form': final_list,
            'current_start_date':fields.Datetime.from_string(str(s_date)).date().strftime('%m/%d/%Y'),
            'current_end_date': fields.Datetime.from_string(str(l_date)).date().strftime('%m/%d/%Y'),
            'last_start_date':fields.Datetime.from_string(str(ps_date)).date().strftime('%m/%d/%Y'),
            'last_end_date': fields.Datetime.from_string(str(pl_date)).date().strftime('%m/%d/%Y'),
        }
        return self.env.ref('sr_sales_report_compmonth.action_report_sales_compmonth_wise').report_action([],data=datas)
