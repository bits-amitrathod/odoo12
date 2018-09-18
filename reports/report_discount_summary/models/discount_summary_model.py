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

from odoo import api, fields, models

class DiscountSummaryView(models.Model):
    _inherit = "sale.order"

    start_date = fields.Date('Start Date' ,store=False)
    test = fields.Char("test ", default='Data',store=False)
    r_discount = fields.Monetary(string='Discount', currency_field='currency_id', compute = '_compute_discount', store=False)
    r_amount = fields.Monetary(string='Amount', currency_field='currency_id', store=False)
    r_total = fields.Monetary(string='Total', currency_field='currency_id', store=False)

    def _compute_discount(self):
        for order in self:
            sum=0
            order.r_discount = order.amount_untaxed
            for r1 in order.order_line:
                sum = sum + (r1.product_uom_qty * r1.price_unit)
            order.r_amount =  order.amount_untaxed
            order.r_discount = sum - order.amount_untaxed
            order.r_total = order.amount_total

