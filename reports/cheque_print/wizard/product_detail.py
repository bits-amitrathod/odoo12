# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018-Today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _

class ProductDetail(models.TransientModel):
    _name = "product.detail"
    _description = "Product Detail"


    start_date = fields.Date(string="Start Date", required='1')
    end_date = fields.Date(string="End Date", required='1')
    top_products = fields.Selection([
        ('by_units', 'Units'),
        ('by_amounts', 'Sales')
    ], string='According to', default = 'by_units')
    no_of_products = fields.Integer(string='Number of Products to Display', default = '5')

    #@api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['start_date', 'end_date', 'top_products', 'no_of_products'])[0]
        print(data['form'])
        return self._print_report(data)


    def _print_report(self, data):
        data['form'].update(self.read(['start_date', 'end_date', 'top_products', 'no_of_products'])[0])
        if data['form']['top_products'] == 'by_units':
            return self.env.ref('tps_report_sale.action_report_products').report_action(self, data=data, config=False)
        else:
            return self.env.ref('tps_report_sale.action_report_products_amount').report_action(self, data=data, config=False)