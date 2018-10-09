# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class inventory_adjustment_report(models.Model):
    _inherit = 'stock.inventory'


    p_sku = fields.Char("SKU/Catalog No", store=False, compute="_calculateSKU")
    p_type= fields.Char("Type", store=False)
    date_cal=fields.Date('Inventory Date',store=False)
    date_posted=fields.Date('Date Posted',store=False)
    amount= fields.Monetary("Amount", store=False,currency_field='currency_id')
    total_amt=fields.Monetary("Total Amount", store=False,currency_field='currency_id')
    p_qty = fields.Integer('Qty', store=False)
    currency_id = fields.Many2one('res.currency', 'Currency', store=False)


    @api.multi
    def _calculateSKU(self):
        scraps = self.env['stock.scrap'].search([])
        ACTIONS = {
            "product": "Stockable Product",
            "consu": "Consumable",
            "service": "Service",

        }

        for order in self:

            order.p_sku = order.product_id.product_tmpl_id.sku_code
            keys=order.product_id.product_tmpl_id.type
            if keys==False:
                keys = "product"
            order.p_type =(ACTIONS[keys])
            order.date_cal=order.date
            order.date_posted=order.date
            order.amount = (float_repr(order.product_id.product_tmpl_id.list_price, precision_digits=2))
            for p in order.line_ids:
                order.p_qty = p.product_qty
                order.total_amt = (float_repr(p.product_qty * order.product_id.product_tmpl_id.list_price, precision_digits=2))

            for user in scraps:
                order.p_sku = user.product_id.product_tmpl_id.sku_code
                keys = user.product_id.product_tmpl_id.type
                if keys == False:
                    keys = "product"
                order.p_type = (ACTIONS[keys])
                order.date_cal = user.create_date
                order.date_posted = user.create_date
                order.p_qty = user.scrap_qty
                order.amount = (float_repr(user.product_id.product_tmpl_id.list_price, precision_digits=2))
                order.total_amt = (
                    float_repr(user.scrap_qty * user.product_id.product_tmpl_id.list_price, precision_digits=2))


    # @api.model
    # def check(self, data):
    #     if data:
    #         return upper(data)
    #     else:
    #         return " "
    #
    # @api.multi
    # def get_report_values(self):
    #     temp = []
    #     ACTIONS = {
    #         "product": "Stockable Product",
    #         "consu": "Consumable",
    #         "service": "Service",
    #     }
    #     scraps = self.env['stock.scrap'].search([])
    #     for user in scraps:
    #         temp_2 = []
    #         temp_2.append(user.product_id.product_tmpl_id.sku_code)
    #         temp_2.append(
    #             datetime.datetime.strptime(str(user.create_date), '%Y-%m-%d %H:%M:%S').date().strftime('%m/%d/%Y'))
    #         temp_2.append(ACTIONS[user.product_id.product_tmpl_id.type])
    #         temp_2.append(user.scrap_qty)
    #         temp_2.append(user.product_id.product_tmpl_id.list_price)
    #         temp_2.append(user.scrap_qty * user.product_id.product_tmpl_id.list_price)
    #         temp.append(temp_2)
    #
    #     adjustment = self.env['stock.inventory.line'].search([])
    #     groupby_dict = {}
    #     filtered_by_date = list(
    #         filter(lambda x: x.inventory_id.date >= self.start_date and x.inventory_id.date <= self.end_date,
    #                adjustment))
    #     _logger.info('AKASH %r', filtered_by_date)
    #     groupby_dict['data'] = filtered_by_date
    #
    #     final_dict = {}
    #     for user in groupby_dict.keys():
    #
    #         for order in groupby_dict[user]:
    #             temp_2 = []
    #             temp_2.append(order.product_id.product_tmpl_id.sku_code)
    #             temp_2.append(
    #                 datetime.datetime.strptime(str(order.create_date), '%Y-%m-%d %H:%M:%S').date().strftime('%m/%d/%Y'))
    #             temp_2.append(ACTIONS[order.product_id.product_tmpl_id.type])
    #             temp_2.append(order.product_qty)
    #             temp_2.append(float_repr(order.product_id.product_tmpl_id.list_price, precision_digits=2))
    #             temp_2.append(
    #                 float_repr(order.product_qty * order.product_id.product_tmpl_id.list_price, precision_digits=2))
    #
    #             temp.append(temp_2)
    #
    #         final_dict['data'] = temp
    #     final_dict['data'].sort(key=lambda x: self.check(x[0]))
    #     datas = {
    #         'ids': self,
    #         'model': 'inventory.adjustment.report',
    #         'form': final_dict,
    #         'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
    #         'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),
    #
    #     }
    #     return self.env.ref('inventory_adjustment_report.action_todo_model_report').report_action([],
    #                                                                                               data=datas)
