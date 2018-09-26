# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_get_engine_order(self, order_id,line_id,set_qty,product_id):
        print(order_id)
        print(self.env['sale.order'].search([('id', '=', order_id)]))
        order=self.env['sale.order'].search([('id', '=', order_id)])[0]
        values={'product_uom_qty':set_qty}
        line=self.env['sale.order.line'].sudo().search([('id', '=', line_id)])[0]
        line.write(values)
        #order.write(line)
        count = self.env['prioritization.engine.model'].get_available_product_count(order.partner_id.id, product_id)
        print(count)
        return count;

