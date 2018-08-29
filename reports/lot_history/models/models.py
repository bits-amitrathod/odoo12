# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime

_logger = logging.getLogger(__name__)
class lot_history(models.TransientModel):
    _name = 'lot_history.lot_history'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date(string="End Date", required=True)
    product_id = fields.Many2many('product.product', string="Products", required=True)

    @api.multi
    def get_report_values(self):
        lots = self.env['stock.production.lot'].search([])
        groupby_dict = {}

        for user in self.product_id:
            filtered_order = list(filter(lambda x: x.product_id == user, lots))
            filtered_by_date = list( filter(lambda x: x.create_date >= self.start_date and x.create_date <= self.end_date, filtered_order))
            groupby_dict[user.name] = filtered_by_date


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
                    temp_2.append(order.name)
                    temp_2.append(order.product_id.product_tmpl_id.sku_code)
                    temp_2.append(order.product_id.product_tmpl_id.name)
                    temp_2.append(ACTIONS[order.product_id.product_tmpl_id.type])
                    temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.name)
                    temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.phone)
                    temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.email)
                    temp_2.append(datetime.datetime.strptime(str(order.create_date),'%Y-%m-%d %H:%M:%S').date().strftime('%m-%d-%Y'))
                    temp.append(temp_2)
                final_dict[user] = temp

        datas = {
            'ids': self,
            'model': 'product.list.report',
            'form': final_dict,
            'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
            'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),

        }
        return self.env.ref('lot_history.action_todo_model_report').report_action([], data=datas)
