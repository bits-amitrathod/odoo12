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
from numpy.core.defchararray import upper
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

class SaleSalespersonReport(models.TransientModel):
    _name = 'custome.product.report'

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
    def print_catalog_vise_report(self):
        sale_orders = self.env['product.product'].search([])
        groupby_dict = {}
        ACTIONS = {
            "product": "Stockable Product",
            "consu": "Consumable",
            "service": "Service",
        }
        # for user in self.product_id:
            # filtered_order = list(filter(lambda x: x.product_id == user, sale_orders))
        filtered_by_date = sale_orders
        groupby_dict['data'] = filtered_by_date

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(ACTIONS[order.product_tmpl_id.type])
                temp_2.append(order.product_tmpl_id.product_brand_id.name)
                temp_2.append(order.product_tmpl_id.sku_code)
                temp_2.append(order.product_tmpl_id.name)
                order.env.cr.execute(
                    "SELECT sum(quantity) as qut FROM public.stock_quant where company_id != 0.0 and  product_id = " + str(
                        order.id))
                query_result = order.env.cr.dictfetchone()
                temp_2.append(query_result['qut'])
                temp_2.append(float_repr(order.product_tmpl_id.list_price,precision_digits=2))
                # temp_2.append(order.product_tmpl_id.name)
                order.env.cr.execute( "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = "+str(order.id))
                query_result = order.env.cr.dictfetchone()
                print(query_result['min'])
                if query_result['min']:
                    temp_2.append(fields.Datetime.from_string(str(query_result['min'])).date().strftime('%m/%d/%Y'))
                else:
                    temp_2.append(query_result['min'])

                if query_result['max']:
                    temp_2.append(fields.Datetime.from_string(str(query_result['max'])).date().strftime('%m/%d/%Y'))
                else:
                    temp_2.append(query_result['max'])

                temp.append(temp_2)
            final_dict[user] = temp
            final_dict['data'].sort(key=lambda x: self.check(x[0]))
        datas = {
            'ids': self,
            'model': 'custome.product.report',
            'form': final_dict,
        }
        return self.env.ref('custom_product_catalog.action_report_custom_catalog_wise').report_action([],
                                                                                                                    data=datas)

    @api.multi
    def print_product_catalog_report(self):
        sale_orders = self.env['product.product'].search([])
        groupby_dict = {}
        filtered_by_date = sale_orders
        groupby_dict['data'] = filtered_by_date

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(order.product_tmpl_id.sku_code)
                temp_2.append(order.name)
                temp_2.append(float_repr(order.product_tmpl_id.list_price,precision_digits=2))
                temp.append(temp_2)
            final_dict[user] = temp
            final_dict['data'].sort(key=lambda x: self.check(x[0]))
        datas = {
            'ids': self,
            'model': 'custome.product.report',
            'form': final_dict,
        }
        return self.env.ref('custom_product_catalog.action_report_product_catalog_wise').report_action([],
                                                                                                      data=datas)

