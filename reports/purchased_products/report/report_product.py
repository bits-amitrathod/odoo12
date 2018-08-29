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

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError



class ReportProductsPurchase(models.AbstractModel):
    _name = 'report.purchased_products.report_products_purchase'
    
    @api.model
    def get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        product_records = {}
        sorted_product_records = []
        Purchases = self.env['purchase.order'].search([('state','in',('purchase','done')),('date_order','>=',docs.start_date),('date_order','<=',docs.end_date)])
        for p in Purchases:
            orders = self.env['purchase.order.line'].search([('order_id','=',p.id)])
            temp = []
            sum = 0
            product_qty = 0
            product_name = ''
            type = ''
            for pol in p.order_line:
                sum = sum + pol.qty_received
                product_name = pol.product_id.name
                type = pol.product_id.default_code
                product_qty =  pol.product_qty
            sorted_product_records.append({'order_id':p.id, 'order_name': p.name ,'state':p.state,'p_name':product_name,'to_qty':int(product_qty),'received':int(sum),'type':type})

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'products': sorted_product_records
        }

