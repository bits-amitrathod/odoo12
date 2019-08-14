# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import _


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_note = fields.Text('Sale Notes')

    carrier_track_ref = fields.Char('Tracking Reference', store=True, readonly=True, compute='_get_carrier_tracking_ref')

    def write(self, val):
        super(sale_order, self).write(val)

        if self.sale_note:
            self.write({'sale_note':False})
            
        if 'sale_note' in val:
            if val['sale_note']:
                body = _(val['sale_note'])
                sale_order_val = {
                    'body': body,
                    'model': 'sale.order',
                    'message_type': 'notification',
                    'no_auto_thread': False,
                    'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                    'res_id': self.id,
                    'author_id': self.env.user.partner_id.id,
                }
                self.env['mail.message'].sudo().create(sale_order_val)
                stock_picking = self.env['stock.picking'].search([('sale_id', '=', self.id)])
                for stk_picking in stock_picking:
                    stock_picking_val = {
                        'body': body,
                        'model': 'stock.picking',
                        'message_type': 'notification',
                        'no_auto_thread': False,
                        'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                        'res_id': stk_picking.id,
                        'author_id': self.env.user.partner_id.id,
                    }
                    self.env['mail.message'].sudo().create(stock_picking_val)

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

    # note = fields.Text('Notes', compute='_get_note')
    #
    # def _get_note(self):
    #     for stock_picking in self:
    #         sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
    #         stock_picking.note = sale_order.sale_note

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
                    sale_order.amount_delivery = self.carrier_price
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
        return action

    @api.one
    def cancel_shipment(self):
        self.carrier_id.cancel_shipment(self)
        msg = "Shipment %s cancelled" % self.carrier_tracking_ref
        self.message_post(body=msg)
        self.carrier_tracking_ref = False
        sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
        sale_order.carrier_track_ref = False

    def update_sale_order_line(self, sale_order, carrier, price_unit):

        sale_order_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id), ('is_delivery', '=', True)])

        if len(sale_order_line) == 1:
            if sale_order.partner_id:
                # set delivery detail in the customer language
                carrier = carrier.with_context(lang=sale_order.partner_id.lang)

            # Apply fiscal position
            taxes = carrier.product_id.taxes_id.filtered(lambda t: t.company_id.id == sale_order.company_id.id)
            taxes_ids = taxes.ids
            if sale_order.partner_id and sale_order.fiscal_position_id:
                taxes_ids = sale_order.fiscal_position_id.map_tax(taxes, carrier.product_id, sale_order.partner_id).ids

            carrier_with_partner_lang = carrier.with_context(lang=sale_order.partner_id.lang)

            if carrier_with_partner_lang.product_id.description_sale:
                so_description = '%s: %s' % (carrier_with_partner_lang.name,
                                             carrier_with_partner_lang.product_id.description_sale)
            else:
                so_description = carrier_with_partner_lang.name

            # Update the sales order line
            sale_order_line.write({'name': so_description, 'price_unit':price_unit,'product_uom': carrier.product_id.uom_id.id, 'product_id': carrier.product_id.id, 'tax_id': [(6, 0, taxes_ids)]})
