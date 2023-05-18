# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class DormantCustomer(models.Model):
    _inherit = "res.partner"

    last_purchase_date = fields.Datetime("Last Purchased Date ", store=False, compute='_compute_last_purchase')
    sale_order=fields.Char("Sales Order#", store=False,compute='_compute_last_purchase')
    # last_purchased_product = fields.Char('Last Purchased Product', store=False)

    #@api.multi
    def _compute_last_purchase(self):
        for customer in self:
            confirmed_sales_orders = self.env['sale.order'].search(
                [('partner_id', '=', customer.id), ('date_order', '!=', False)]).sorted(
                key=lambda o: o.date_order)
            if len(confirmed_sales_orders) > 0:
                length=len(confirmed_sales_orders)-1
                customer.last_purchase_date = confirmed_sales_orders[length].date_order
                customer.sale_order= confirmed_sales_orders[length].name
            else:
                customer.sale_order = ""
                customer.last_purchase_date = None
                # sales_order_lines = confirmed_sales_orders[0].order_line
                # for order_line in sales_order_lines:
                #     customer.last_purchased_product = order_line.product_id.product_tmpl_id.name
                #     break