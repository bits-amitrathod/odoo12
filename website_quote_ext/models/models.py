# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    min_exp_date = fields.Date(compute='_compute_exp_dates', store=False)
    max_exp_date = fields.Date(compute='_compute_exp_dates', store=False)

    def _compute_exp_dates(self):
        for product in self:
            if product.id:
                query = """
                    SELECT
                        sum(quantity), min(use_date), max(use_date)
                    FROM
                        stock_quant
                    INNER JOIN
                        stock_production_lot
                    ON
                        (stock_quant.lot_id = stock_production_lot.id)
                    INNER JOIN
                        stock_location
                    ON
                        (stock_quant.location_id = stock_location.id)
                    WHERE
                        stock_location.usage IN ('internal', 'transit')
                        AND stock_production_lot.product_id = %s
                """
                self.env.cr.execute(query, (product.id,))
                result = self.env.cr.fetchone()

                if result and all(result):
                    product.min_exp_date = result[1]
                    product.max_exp_date = result[2]
                else:
                    product.min_exp_date = False
                    product.max_exp_date = False
class Website(models.Model):
    _inherit = 'website'

    def sale_get_engine_order(self, order_id, line_id, set_qty, product_id):

        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        values = {'product_uom_qty':set_qty}
        line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])[0]
        line.write(values)
        customer = self.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)])[0]
        cust_id = order.partner_id.id
        if customer.is_parent is False:
            cust_id = customer.parent_id
        count = self.env['prioritization.engine.model'].get_available_product_count(cust_id, product_id)
        return count;

    def sale_get_engine_count(self, order_id, product_id):
        order = self.env['sale.order'].search([('id', '=', order_id)])[0]
        customer = self.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)])[0]
        cust_id = order.partner_id.id
        if customer.is_parent is False:
            cust_id = customer.parent_id
        count = self.env['prioritization.engine.model'].get_available_product_count(cust_id, product_id)
        return count;

    def sale_order_line_del(self, order_id, line_id, product_id):
        line = self.env['sale.order.line'].search([('id', '=', line_id)])[0]
        line.unlink()
        '''customer = self.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)])[0]
        cust_id = order.partner_id.id
        if customer.is_parent is False:
            cust_id = customer.parent_id
        count = self.env['prioritization.engine.model'].get_available_product_count(cust_id, product_id)
        return count;'''

