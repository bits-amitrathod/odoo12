from odoo import models, api,_
import logging

_logger = logging.getLogger(__name__)


class StockBackorder(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        action = super(StockBackorder, self).process()

        for picking in self.pick_ids:
            if picking.picking_type_id.code == "outgoing":
                if picking.state == 'done' and picking.carrier_id and picking.carrier_tracking_ref:
                    sale_order = self.env['sale.order'].search([('name', '=', picking.origin)])
                    sale_order.carrier_track_ref = picking.carrier_tracking_ref
                    if sale_order.carrier_id.id is False:
                        sale_order.carrier_id = picking.carrier_id.id
                        sale_order.delivery_price = picking.carrier_price
                    if sale_order.carrier_id.id != picking.carrier_id.id:
                        sale_order.carrier_id = picking.carrier_id.id
                        sale_order.delivery_price = picking.carrier_price
                        sale_order.amount_delivery = picking.carrier_price
                        self.update_sale_order_line(sale_order, picking.carrier_id, picking.carrier_price)
        return action

    def process_cancel_backorder(self):
        action = super(StockBackorder, self).process_cancel_backorder()

        for picking in self.pick_ids:
            if picking.picking_type_id.code == "outgoing":
                if picking.state == 'done' and picking.carrier_id and picking.carrier_tracking_ref:
                    sale_order = self.env['sale.order'].search([('name', '=', picking.origin)])
                    sale_order.carrier_track_ref = picking.carrier_tracking_ref
                    if sale_order.carrier_id.id is False:
                        sale_order.carrier_id = picking.carrier_id.id
                        sale_order.delivery_price = picking.carrier_price
                    if sale_order.carrier_id.id != picking.carrier_id.id:
                        sale_order.carrier_id = picking.carrier_id.id
                        sale_order.delivery_price = picking.carrier_price
                        sale_order.amount_delivery = picking.carrier_price
                        self.update_sale_order_line(sale_order, picking.carrier_id, picking.carrier_price)
        return action

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
