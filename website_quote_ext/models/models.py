# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_get_engine_order(self, order_id,force_create=False, code=None, update_pricelist=False, force_pricelist=False):
        sale_order =self.env['sale.order'].sudo().browse(order_id)
        print(sale_order)
        return sale_order;