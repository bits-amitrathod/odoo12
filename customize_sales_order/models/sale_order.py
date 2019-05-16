# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_note = fields.Text('Sale Notes')

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    note = fields.Text('Notes', compute='_get_note')

    def _get_note(self):
        sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
        self.note = sale_order.sale_note






