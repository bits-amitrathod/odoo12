# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class inventory_adjustment_report(models.TransientModel):
    _name = 'inventory.adjustment.report'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)



    @api.multi
    def get_report_values(self):
        adjustment = self.env['stock.inventory.line'].search([])
        _logger.info('AKASH %r', adjustment)
        groupby_dict = {}
        filtered_by_date = list(
            filter(lambda x: x.inventory_id.date >= self.start_date and x.inventory_id.date <= self.end_date, adjustment))
        _logger.info('AKASH %r', filtered_by_date)
        groupby_dict['data'] = filtered_by_date
        ACTIONS = {
            "product": "Stockable Product",
            "consu": "Consumable",
            "service": "Service",
        }
        final_dict = {}
        for user in groupby_dict.keys():
            temp = []
            for order in groupby_dict[user]:
                temp_2 = []
                temp_2.append(order.product_name)
                temp_2.append(datetime.datetime.strptime(str(order.create_date),'%Y-%m-%d %H:%M:%S').date().strftime( '%m/%d/%Y'))
                temp_2.append(ACTIONS[order.product_id.product_tmpl_id.type])
                temp_2.append(order.product_qty)
                temp_2.append(float_repr(order.product_id.product_tmpl_id.list_price,precision_digits=2))
                temp_2.append(float_repr(order.product_qty*order.product_id.product_tmpl_id.list_price,precision_digits=2))
                temp_2.append(order.product_id.product_tmpl_id.sku_code)

                temp.append(temp_2)
            final_dict[user] = temp
        datas = {
            'ids': self,
            'model': 'inventory.adjustment.report',
            'form': final_dict,
            'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
            'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),

        }
        return self.env.ref('inventory_adjustment_report.action_todo_model_report').report_action([],
                                                                                               data=datas)

