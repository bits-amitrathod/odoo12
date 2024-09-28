# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    note_readonly_flag = fields.Integer('Delivery Note readonly flag', default=0)
    # note = fields.Text('Notes', compute='_get_note')
    #
    # def _get_note(self):
    #     for stock_picking in self:
    #         sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
    #         stock_picking.note = sale_order.sale_note

    def button_validate(self):
        action = super(StockPicking, self).button_validate()

        # Note Section code
        if self.sale_id:
            picking_conditions = {
                "Pick": "Pull",
                "Pull": "Delivery Orders"
            }
            if self.state == "done":
                self.note_readonly_flag = 1
                # self.add_note_in_log_section()
                if self.picking_type_id.name == "Pick" or self.picking_type_id.name == "Pull":
                    for picking_id in self.sale_id.picking_ids:
                        if picking_id.state != 'cancel' and picking_id.state == 'assigned' and \
                                (picking_id.picking_type_id.name == picking_conditions.get(self.picking_type_id.name)):
                            picking_id.note = self.note

        if self.picking_type_id.code == "outgoing":
            if self.state == 'done' and self.carrier_id and self.carrier_tracking_ref:
                sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
                sale_order.carrier_track_ref = self.carrier_tracking_ref
                if sale_order.carrier_id.id is False:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.amount_delivery = self.carrier_price
                    sale_order.set_delivery_line(self.carrier_id, self.carrier_price)
                if sale_order.carrier_id.id != self.carrier_id.id:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.amount_delivery = self.carrier_price
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
                else:
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
        return action

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

    def add_note_in_log_section(self):
        if self.note:
            body = self.note
            for stk_picking in self.sale_id.picking_ids:
                stock_picking_val = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'reply_to_force_new': False,
                    'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note', raise_if_not_found=True),
                    'res_id': stk_picking.id,
                    'author_id': self.env.user.partner_id.id,
                }
                self.env['mail.message'].sudo().create(stock_picking_val)