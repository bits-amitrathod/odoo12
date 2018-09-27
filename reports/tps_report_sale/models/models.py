# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
_logger = logging.getLogger(__name__)
class tps_report_sale(models.Model):
    _inherit = 'sale.order'

    p_sku = fields.Char("Product SKU", store=False, compute="_calculateSKU")
    product_name = fields.Char("Product Name", store=False)
    t_qty = fields.Integer('Total Quantity', store=False)
    t_amt = fields.Monetary('Total Quantity', store=False)


    @api.multi
    def _calculateSKU(self):

        for order in self:
            for p in order.order_line:
                order.p_sku =p.product_id.product_tmpl_id.sku_code
                order.product_name=p.product_id.product_tmpl_id.name
                order.t_qty = p.product_uom_qty
                order.t_amt = p.price_subtotal


    # @api.model
    # def get_report_values(self, docids, data):
    #     self.model = self.env.context.get('active_model')
    #     docs = self.env['product.detail'].browse(self.env.context.get('active_id'))
    #     product_records = {}
    #     sorted_product_records = []
    #     sales = self.env['sale.order'].search([('state', 'in', ('sale', 'done')), ('date_order', '>=', docs.start_date),
    #                                            ('date_order', '<=', docs.end_date)])
    #     for s in sales:
    #         orders = self.env['sale.order.line'].search([('order_id', '=', s.id)])
    #         for order in orders:
    #             if order.product_id:
    #                 if order.product_id not in product_records:
    #                     infoData = [0, 0, ' ']
    #                     infoData[2] = order.product_id.product_tmpl_id.sku_code
    #                     product_records.update({order.product_id: infoData})
    #                 product_records[order.product_id][0] += order.product_uom_qty
    #                 product_records[order.product_id][1] += order.price_subtotal
    #
    #     for product_id, product_uom_qty in sorted(product_records.items(), key=lambda kv: kv[1], reverse=True):
    #         sorted_product_records.append(
    #             {'sku': product_uom_qty[2], 'name': product_id.name, 'qty': int(product_uom_qty[0]),
    #              'desc': 'Description', 'sale_amt': float_repr(product_uom_qty[1], precision_digits=2)})
    #
    #     sorted_product_records.sort(key=lambda x: self.check(x['sku']))
    #     return {
    #         'doc_ids': self.ids,
    #         'doc_model': self.model,
    #         'docs': docs,
    #         'start_date': fields.Datetime.from_string(str(docs.start_date)).date().strftime('%m/%d/%Y'),
    #         'end_date': fields.Datetime.from_string(str(docs.end_date)).date().strftime('%m/%d/%Y'),
    #         'time': time,
    #         'products': sorted_product_records