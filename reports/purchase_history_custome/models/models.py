# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)


class purchase_history(models.Model):

    _inherit = 'purchase.order'



    sku = fields.Char("SKU/Catalog No", store=False, compute="_calculateSKU1")
    vendor = fields.Char("Vendor", store=False)
    qty = fields.Integer("Qty", store=False)
    manufacturer_rep = fields.Char("Manufacturer", store=False)
    product_name=fields.Char("Product Name", store=False)
    minExpDate = fields.Date("Min Exp Date", store=False, compute="_calculateDate1")
    maxExpDate = fields.Date("Max Exp Date", store=False, compute="_calculateDate2")
    unit_price=fields.Monetary("Price Per Stock", store=False)


    @api.multi
    def _calculateSKU1(self):
        for order in self:

            for p in order.order_line:
                order.sku = p.product_id.product_tmpl_id.sku_code
                order.vendor = p.partner_id.name
                order.manufacturer_rep = p.partner_id.name
                order.product_name = p.product_id.product_tmpl_id.name
                order.qty = p.product_qty
                order.unit_price = (float_repr(p.price_unit, precision_digits=2))



    @api.onchange('minExpDate')
    def _calculateDate1(self):

        for order in self:

            if order.product_id.id!=False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = self.env.cr.dictfetchone()
                order.minExpDate = query_result['min']



    @api.onchange('maxExpDate')
    def _calculateDate2(self):
        for order in self:

            if order.product_id.id != False:
                order.env.cr.execute("SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
                query_result = order.env.cr.dictfetchone()
                order.maxExpDate = query_result['max']





    # _logger.info('################ABCDfffffffffffffffffffffffffffffff')
    # for order in self:
    #     for p1 in order.order_line:
    #         _logger.info('################ABCDfffffffffffffffffffffffffffffff')
    #         order.sku = p1.product_id.product_tmpl_id.sku_code
    #         order.vendor = p1.partner_id.name
    #         order.manufacturer_rep = p1.partner_id.name
    #         order.product_name = p1.product_id.product_tmpl_id.name
    #         order.qty = p1.product_qty
    #         order.unit_price = (float_repr(p1.price_unit, precision_digits=2))

    # @api.onchange('start_date')
    # def _startDate(self):
    #     start_date=self.start_date
    #
    # @api.onchange('end_date')
    # def _endDate(self):
    #     end_date = self.start_date


    # start_date = fields.Date('Start Date', required=True)
    # end_date = fields.Date(string="End Date", required=True)
    # product_id = fields.Many2many('product.product',string="Products",required=True)
    #
    #
    #
    #
    #
    # @api.model
    # def check(self, data):
    #     if data:
    #         return upper(data)
    #     else:
    #         return " "
    #
    # @api.multi
    # def get_report_values(self):
    #     purchase_orders = self.env['purchase.order.line'].search([])
    #     groupby_dict = {}
    #     for user in self.product_id:
    #         filtered_order = list(filter(lambda x: x.product_id == user, purchase_orders))
    #         filtered_by_date = list( filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, filtered_order))
    #         groupby_dict[user.name] = filtered_by_date
    #
    #     final_dict = {}
    #     for user in groupby_dict.keys():
    #         temp = []
    #         for order in groupby_dict[user]:
    #             temp_2 = []
    #             temp_2.append(order.product_id.product_tmpl_id.sku_code)
    #             temp_2.append(order.partner_id.name)
    #             temp_2.append(order.product_id.product_tmpl_id.name)
    #             temp_2.append(order.product_qty)
    #             temp_2.append(float_repr(order.price_unit, precision_digits=2))
    #             order.env.cr.execute(
    #                 "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id =" + str(
    #                     order.product_id.id))
    #             query_result = order.env.cr.dictfetchone()
    #             if query_result['min'] != None:
    #                 temp_2.append(fields.Datetime.from_string(str(query_result['min'])).date().strftime('%m/%d/%Y'))
    #             else:
    #                 temp_2.append(query_result['min'])
    #             if query_result['max'] != None:
    #                 temp_2.append(fields.Datetime.from_string(str(query_result['max'])).date().strftime('%m/%d/%Y'))
    #             else:
    #                 temp_2.append(query_result['max'])
    #
    #             temp.append(temp_2)
    #         final_dict[user] = temp
    #     final_dict[user].sort(key=lambda x: self.check(x[0]))
    #
    #     datas = {
    #         'ids': self,
    #         'model': 'purchase.history.cust',
    #         'form': final_dict,
    #         'start_date': fields.Datetime.from_string(str(self.start_date)).date().strftime('%m/%d/%Y'),
    #         'end_date': fields.Datetime.from_string(str(self.end_date)).date().strftime('%m/%d/%Y'),
    #     }
    #
    #     # return self.env.ref('purchase_history_custome.action_todo_model_report').report_action([],data=datas)
    #     # return {
    #     #     'doc_ids': datas.get('ids'),
    #     #     'doc_model': datas.get('model'),
    #     #     'data': datas,
    #     # }
    #     return self.env.ref
    #     {
    #         'name': 'Purchase',
    #         'view_type': 'tree',
    #         "view_mode": 'tree,form',
    #         'res_model': 'purchase.history.cust',
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'data': 'datas',
    #         'view_id':'action_form_view_wizard',
    #     }
