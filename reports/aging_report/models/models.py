# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import  datetime
from datetime import datetime

_logger = logging.getLogger(__name__)
class aging_report(models.Model):
    _inherit = 'stock.production.lot'

    pr_sku = fields.Char("SKU/Catalog No", store=False, compute="_calculateSKU")
    pr_name= fields.Char("Product Name", store=False)
    tracking = fields.Char("Tracking", store=False,compute="_calculateTracking")
    p_qty = fields.Integer('Qty', store=False)
    cr_date = fields.Date("Created date", store=False)
    days = fields.Char("Days", store=False)
    maxExpDate = fields.Date("Max Exp Date", store=False, compute="_calculateDate2")

    # @api.onchange('days')
    # def _calculateDays(self):
    #     DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    #     for order in self:
    #         to_dt=datetime.datetime.strptime(fields.date.today(), '%Y-%m-%d %H:%M:%S')
    #         from_dt = datetime.strptime(order.create_date, DATETIME_FORMAT)
    #         to_dt = datetime.strptime(fields.date.today(), DATETIME_FORMAT)
    #         timedelta = to_dt - from_dt
    #         # order.days = timedelta.days + float(timedelta.seconds) / 86400



    @api.onchange('maxExpDate')
    def _calculateDate2(self):
        for order in self:

            if order.product_id.id != False:
                order.env.cr.execute(
                    "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                        order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                order.maxExpDate = query_result['max']

    @api.onchange('tracking')
    def _calculateTracking(self):
        for order in self:
            if order.maxExpDate==False:
                order.maxExpDate=''
            order.tracking = 'Lot#:' + str(order.name)

    @api.multi
    def _calculateSKU(self):

        for order in self:

            order.pr_sku = order.product_id.product_tmpl_id.sku_code
            order.pr_name=order.product_id.product_tmpl_id.name
            order.tracking = 'Lot#:' + str(order.name)
            # order.cr_date = order.create_date



            for p in order.quant_ids:
                order.p_qty = p.quantity

            # order.cr_date=order.create_date
            # order.vend=order.product_id.product_tmpl_id.product_brand_id.partner_id.name
            # order.ph=order.product_id.product_tmpl_id.product_brand_id.partner_id.phone
            # order.email = order.product_id.product_tmpl_id.product_brand_id.partner_id.email
            # for p in order.quant_ids:
            #     order.p_qty = p.quantity
    # @api.multi
    # def get_report_values(self):
    #     lots = self.env['stock.production.lot'].search([])
    #     groupby_dict = {}
    #
    #     for user in self.product_id:
    #         filtered_order = list(filter(lambda x: x.product_id == user, lots))
    #         filtered_by_date = list( filter(lambda x: x.create_date >= self.start_date and x.create_date <= self.end_date, filtered_order))
    #         groupby_dict[user.name] = filtered_by_date
    #
    #
    #         final_dict = {}
    #         for user in groupby_dict.keys():
    #             temp = []
    #             for order in groupby_dict[user]:
    #                 temp_2 = []
    #                 temp_2.append(order.product_id.product_tmpl_id.sku_code)
    #                 temp_2.append(order.name)
    #                 temp_2.append(order.product_id.product_tmpl_id.name)
    #                 temp_2.append(datetime.datetime.strptime(str(order.create_date), '%Y-%m-%d %H:%M:%S').date().strftime('%m-%d-%Y'))
    #                 temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.name)
    #                 temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.phone)
    #                 temp_2.append(order.product_id.product_tmpl_id.product_brand_id.partner_id.email)
    #
    #                 temp.append(temp_2)
    #             final_dict[user] = temp
    #
    #     datas = {
    #         'ids': self,
    #         'model': 'product.list.report',
    #         'form': final_dict,
    #         'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
    #         'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),
    #
    #     }
    #     return self.env.ref('aging_report.action_todo_model_report').report_action([], data=datas)
