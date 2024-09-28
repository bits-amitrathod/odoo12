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
from odoo import api, models
import logging

log = logging.getLogger(__name__)

class apprisal_tracker_vendor_report(models.AbstractModel):
    _name = 'report.appraisal_tracker.appraisal_tracker_report'
    _description = 'Appraisal Tracker Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        purchase_orders=[]
        # if not docids:
        #     purchase_orders = self.env['purchase.order'].search([('state', 'in', ('purchase','cancel')),('status','in',('purchase','cancel'))])
        # else:
        # purchase_orders = self.env['purchase.order'].browse(docids)
        purchase_orders = self.env['purchase.order'].with_context(vendor_offer_data=True).browse(docids)

        print('===========================================  =')
        print(purchase_orders)
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data':purchase_orders,
        }
