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
import collections

from builtins import reversed

from odoo import api, fields, models
from odoo.tools import float_repr
import datetime
from numpy.core.defchararray import upper
import collections



class SaleSalespersonReport(models.TransientModel):
    _name = 'sale.product.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products", required=True)

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "
    @api.multi
    def print_salesperson_vise_report(self):
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        groupby_dict = collections.OrderedDict()
        final_list = []
        for p_id in self.product_id:
            # filtered_order = list(filter(lambda x: x.product_id == user, sale_orders))
            filtered_by_date = list(filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, sale_orders))
            # groupby_dict[user.name] = filtered_by_date
            temp = []
            list1 = []
            for sale_order in filtered_by_date:
                for sale_order_line in sale_order.order_line:
                    if p_id == sale_order_line.product_id :
                        temp_2 = []
                        temp_2.append(sale_order.name)
                        temp_2.append(datetime.datetime.strptime(sale_order.date_order, "%Y-%m-%d %H:%M:%S").date().strftime('%m/%d/%Y'))
                        temp_2.append(float_repr(sale_order_line.price_subtotal,precision_digits=2))
                        temp.append(temp_2)

            list1.append(p_id.name)
            list1.append(sorted(temp, key=lambda x: x[0],reverse=False))
            final_list.append(list1)

        final_list.sort(key = lambda x: self.check(x[0]))

        datas = {
            'ids': self,
            'model': 'sale.product.reprt',
            'form': final_list,
            'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
            'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),

        }
        action = self.env.ref('sr_sales_report_product_groupby.action_report_sales_saleperson_wise').report_action([],
                                                                                                                    data=datas)
        action.update({'target': 'main'})
        return action

