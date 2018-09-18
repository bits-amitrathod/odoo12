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


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_price_list.price_list_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.template'].browse(docids)}


class CustProductPriceList(models.AbstractModel):
    _name = 'report.report_price_list.cust_price_list_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {'data': self.env['product.template'].browse(docids)}