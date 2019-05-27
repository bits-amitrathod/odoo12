# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_note = fields.Text('Sale Notes')

    carrier_track_ref = fields.Char('Tracking Reference', store=True, readonly=True, compute='_get_carrier_tracking_ref')

    @api.one
    def _get_carrier_tracking_ref(self):
        for so in self:
            stock_picking = self.env['stock.picking'].search([('origin', '=', so.name), ('picking_type_id', '=', 5),
                                                              ('state', 'in', ['done', 'waiting', 'assigned'])])
            for sp in stock_picking:
                if sp.carrier_tracking_ref:
                    so.carrier_track_ref = sp.carrier_tracking_ref
                    break
            break

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    note = fields.Text('Notes', compute='_get_note')

    def _get_note(self):
        for stock_picking in self:
            sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
            stock_picking.note = sale_order.sale_note