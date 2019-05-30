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

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    note = fields.Text('Notes', compute='_get_note')

    def _get_note(self):
        for stock_picking in self:
            sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
            stock_picking.note = sale_order.sale_note

    @api.multi
    def button_validate(self):

        action = super(StockPicking, self).button_validate()

        if self.picking_type_id.code == "outgoing":
            if self.state == 'done' and self.carrier_id and self.carrier_tracking_ref:
                sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
                sale_order.carrier_track_ref = self.carrier_tracking_ref
                if sale_order.carrier_id.id is False:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.delivery_price = self.carrier_price
                if sale_order.carrier_id.id != self.carrier_id.id:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.delivery_price = self.carrier_price
        return action

    @api.one
    def cancel_shipment(self):
        self.carrier_id.cancel_shipment(self)
        msg = "Shipment %s cancelled" % self.carrier_tracking_ref
        self.message_post(body=msg)
        self.carrier_tracking_ref = False
        sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
        sale_order.carrier_track_ref = False