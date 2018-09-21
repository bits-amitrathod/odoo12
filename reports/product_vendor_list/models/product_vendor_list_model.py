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


class ProductVendorListView(models.Model):
    _inherit = 'purchase.order'

    last_sold = fields.Date('Last Sold',  store=False)
    cost=fields.Monetary(string='Cost', store=False)
    sku_code_product = fields.Char(string='Product Number', compute='_compute_product_vals', store=False)

    @api.onchange('cost')
    def _compute_product_vals(self):

        for order in self:
            product = self.env['product.product'].search([('id', '=', order.product_id.id)])
            order.sku_code_product=product.sku_code
            order.cost=product.list_price
            # order = "confirmation_date desc", limit = 1
            sale_orders = self.env['sale.order'].search([('product_id', '=', order.product_id.id), ('state', '=', 'sale')])
            if(sale_orders.confirmation_date):
                order.last_sold=fields.Datetime.from_string(sale_orders.confirmation_date).date()
