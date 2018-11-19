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
import json


class ReportInventoryProductValuationSummary(models.AbstractModel):
    _name = 'report.inventory_valuation_summary.inventory_valuation_template'

    @api.model
    def get_report_values(self, docids, data=None):
        self.env.cr.execute("""
            SELECT warehouse|| '/'|| location as warehouse, array_agg(ARRAY[ type, products]) as type
            from(SELECT  warehouse, type,location, string_agg(concat_ws(';', name, quantity,unit_cost,asset_value,currency_id),',') as products
                FROM public.inventory_valuation_summary Group by warehouse,type,location) as tbl Group by warehouse,location
                          """)

        warehouses = self.env.cr.dictfetchall()
        return {
            'warehouses': warehouses
        }
