# -*- coding: utf-8 -*-

from odoo import models, fields, api
from numpy.core.defchararray import upper
import logging
import datetime
from odoo.tools import float_repr

_logger = logging.getLogger(__name__)


class purchase_history(models.TransientModel):
    _name = 'purchase.history.cust'

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
    def get_report_values(self):
        purchase_orders = self.env['purchase.order.line'].search([])
        groupby_dict = {}
        for user in self.product_id:
            filtered_order = list(filter(lambda x: x.product_id == user, purchase_orders))
            filtered_by_date = list( filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, filtered_order))
            groupby_dict[user.name] = filtered_by_date

        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(order.product_id.product_tmpl_id.sku_code)
                temp_2.append(order.partner_id.name)
                temp_2.append(order.product_id.product_tmpl_id.name)
                temp_2.append(order.product_qty)
                temp_2.append(float_repr(order.price_unit, precision_digits=2))
                order.env.cr.execute(
                    "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                        order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                if query_result['min'] != None:
                    temp_2.append(fields.Datetime.from_string(str(query_result['min'])).date().strftime('%m/%d/%Y'))
                else:
                    temp_2.append(query_result['min'])
                if query_result['max'] != None:
                    temp_2.append(fields.Datetime.from_string(str(query_result['max'])).date().strftime('%m/%d/%Y'))
                else:
                    temp_2.append(query_result['max'])

                temp.append(temp_2)
            final_dict[user] = temp
        final_dict[user].sort(key=lambda x: self.check(x[0]))

        datas = {
            'ids': self,
            'model': 'purchase.history.cust',
            'form': final_dict,
            'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
            'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),

        }
        return self.env.ref('purchase_history_custome.action_todo_model_report').report_action([],
                                                                                               data=datas)
