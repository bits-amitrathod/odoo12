# -*- coding: utf-8 -*-

import logging
import time
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FixStockValuationLayerScheduler(models.Model):
    _name = "fix.stock.valuation.layer.cron"

    @api.model
    def fix_stock_valuation_layer_scheduler(self,prods_sku):
        _logger.info('In fix stock valuation layer scheduler ')
        company = self.env.company
        start_time = time.time()
        count_of_prod = 0
        rows_corrected = 0
        if len(prods_sku) == 10 and prods_sku == 'fixallprod':
            products = self.env['product.product'].search([('active', 'in', [True, False])])
        else:
            products = self.env['product.product'].search([('default_code', 'in', prods_sku)])

        for product in products:
            prod_id = product.id
            unit_cost = 0
            quantity = 0
            new_quantity = 0
            value = 0
            new_value = 0
            value_at_prod = 0
            domain = [
                ('product_id', '=', prod_id),
                ('company_id', '=', company.id),
            ]
            groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum', 'quantity:sum'], ['product_id'])

            for group in groups:
                value = round(self.env.company.currency_id.round(group['value']),2)
                quantity = group['quantity']

            if groups!=[]:
                unit_cost = product.standard_price
                value_at_prod = round(product.qty_available * product.standard_price,2)
                vals = {
                    'product_id': prod_id,
                    'unit_cost': unit_cost,
                    'quantity': 0,
                    'value': 0,
                    'remaining_qty': 0,
                    'company_id': company.id,
                    'description': 'SPS : fix stock valuation layer',
                }
                if quantity != product.qty_available:
                    new_quantity = product.qty_available - quantity
                    vals["quantity"] = new_quantity

                if value != value_at_prod:
                    new_value = value_at_prod - value
                    vals["value"] = new_value

                if (quantity != product.qty_available) or (value != value_at_prod):
                    count_of_prod = count_of_prod +1
                    adjustment_value = self.env['stock.valuation.layer'].sudo().create(vals)

                svls_to_fix = self.env['stock.valuation.layer'].sudo().search([
                    ('product_id', '=',prod_id),
                    ('remaining_qty', '<', 0),
                    ('stock_move_id', '!=', False),
                    ('company_id', '=', company.id),
                ], order='create_date, id')

                for svl in svls_to_fix:
                    new_vals = {
                        'remaining_qty': 0,
                        'remaining_value': 0,
                    }
                    rows_corrected = rows_corrected+1
                    svl.write(new_vals)

            groups_rem = self.env['stock.valuation.layer'].read_group(domain, ['remaining_value:sum', 'remaining_qty:sum'], ['product_id'])

            for group_re in groups_rem:
                value_re = round(self.env.company.currency_id.round(group_re['remaining_value']), 2)
                quantity_re = group_re['remaining_qty']

            if groups_rem != []:
                unit_cost = product.standard_price
                value_at_prod = round(product.qty_available * product.standard_price, 2)
                vals_re = {
                    'product_id': prod_id,
                    'unit_cost': unit_cost,
                    'quantity': 0,
                    'value': 0,
                    'remaining_qty': 0,
                    'company_id': company.id,
                    'description': 'SPS : fix stock valuation layer remaining qty',
                }
                if quantity_re != product.qty_available:
                    new_quantity_re = product.qty_available - quantity_re
                    vals_re["remaining_qty"] = new_quantity_re

                # if value_re != value_at_prod:
                #     new_value_re = value_at_prod - value_re
                #     vals_re["remaining_value"] = new_value_re

                if (quantity_re != product.qty_available) or (value_re != value_at_prod):
                    count_of_prod = count_of_prod + 1
                    adjustment_value_re = self.env['stock.valuation.layer'].sudo().create(vals_re)

        _logger.info("--- %s seconds ---", (time.time() - start_time))
        _logger.info('count_of_prod %s ', count_of_prod)
        _logger.info('rows_corrected %s ', rows_corrected)
