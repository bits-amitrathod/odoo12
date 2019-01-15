from odoo import api, fields, models ,_
import datetime

class PurchaseOrderPopUp(models.TransientModel):
    _name = 'purchase.order.shipping.popup'
    _description = 'Shipping Label Generation'

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', required=True, ondelete='cascade')
    product_packaging = fields.Many2one('product.packaging', string='Package', default=False)
    weight = fields.Float('Weight')

    def action_tracking(self):
        self.ensure_one()
        order=self.env['purchase.order'].browse(self._context['active_id'])
        res=self.carrier_id.fedex_send_shipping_label(order,self)
        msg = _("Shipment sent to carrier Fedex US for shipping with tracking number ")
        order.message_post(body=msg)


