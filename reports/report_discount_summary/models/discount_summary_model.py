from odoo import api, fields, models


class DiscountSummaryView(models.Model):
    _inherit = "sale.order"

    start_date = fields.Date('Start Date', store=False)
    r_line_item = fields.Integer("Line #", store=False)
    r_discount = fields.Monetary(string='Discount', currency_field='currency_id', compute='_compute_discount',
                                 store=False)
    r_amount = fields.Monetary(string='Amount', currency_field='currency_id', store=False)

    # r_total = fields.Monetary(string='Total', currency_field='currency_id', store=False)

    def _compute_discount(self):
        for order in self:
            sum = 0
            order.r_line_item = len(order.order_line)
            for r1 in order.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)
            order.r_amount =  order.amount_untaxed
            order.r_discount = sum - order.amount_untaxed
            # order.r_total = order.amount_total
