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

class SaleSalespersonReport(models.TransientModel):
    _name = 'product.list.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    user_ids = fields.Many2many('res.users', string="Salesperson")

    @api.model
    def check(self, data):
        if data:
            return upper(data)
        else:
            return " "

    @api.multi
    def print_product_price_list_vise_report(self):
        sale_orders = self.env['product.product'].search([])
        groupby_dict = {}
        filtered_order = sale_orders
        filtered_by_date = filtered_order
        groupby_dict['data'] = filtered_by_date

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for product in groupby_dict[user]:
                temp_2 = []
                temp_2.append(product.product_tmpl_id.sku_code)
                temp_2.append(product.product_tmpl_id.name)
                temp_2.append(float_repr(product.product_tmpl_id.standard_price,precision_digits=2))
                temp.append(temp_2)
            final_dict[user] = temp

        final_dict['data'].sort(key=lambda x:self.check(x[0]))
        datas = {
            'ids': self,
            'model': 'product.list.report',
            'form': final_dict,
            'start_date': self.start_date,
            'end_date': self.end_date,

        }
        return self.env.ref('product_price_list_report.action_report_price_list_wise').report_action([], data=datas)

    @api.multi
    def print_customer_product_price_list_vise_report(self):
        sale_orders = self.env['product.product'].search([])
        groupby_dict = {}
        filtered_order = sale_orders
        filtered_by_date = filtered_order
        groupby_dict['data'] = filtered_by_date

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for product in groupby_dict[user]:
                temp_2 = []
                temp_2.append(product.product_tmpl_id.sku_code)
                temp_2.append(product.product_tmpl_id.name)
                temp_2.append(float_repr(product.product_tmpl_id.list_price, precision_digits=2))
                temp.append(temp_2)
            final_dict[user] = temp
        final_dict['data'].sort(key=lambda x: self.check(x[0]))
        datas = {
            'ids': self,
            'model': 'product.list.report',
            'form': final_dict,
            'start_date': self.start_date,
            'end_date': self.end_date,

        }
        return self.env.ref('product_price_list_report.action_report_cust_price_list_wise').report_action([], data=datas)

