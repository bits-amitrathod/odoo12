from odoo import api, fields, models ,_
import datetime
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrderPopUp(models.TransientModel):
    _name = 'purchase.order.shipping.popup'

    def _get_default_carrier(self):
        carrier = self.env['delivery.carrier'].search([('name', '=', 'Vendor_Fedex Ground')])
        if carrier:
            return carrier.id

    def _get_default_packaging(self):
        packing = self.env['product.packaging'].search([('name', '=', 'FEDEX_YOUR_PACKAGING')])
        if packing:
            return packing.id

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', required=True, ondelete='cascade',
                                 domain="[('delivery_type','=','fedex')]", default=_get_default_carrier)
    product_packaging = fields.Many2one('product.packaging', string='Package',
                                        domain="[('package_carrier_type','=','fedex')]", default=_get_default_packaging)
    weight = fields.Float('Weight', default=5.00)
    package_count = fields.Integer("Packages Count", default=1)

    @api.constrains('package_count')
    @api.one
    def _check_package_count(self):
        if self.package_count:
            package_count = self.package_count
            if package_count <= 0:
                raise ValidationError(
                    _('Packages Count field should be greater than 0'))


    def action_tracking(self):
        self.ensure_one()
        order=self.env['purchase.order'].browse(self._context['active_id'])
        res=self.carrier_id.fedex_send_shipping_label(order,self)
        '''order_currency = order.currency_id
            msg = _("Shipment sent to carrier %s for shipping with tracking number %s<br/>Cost: %.2f %s") % (
                self.carrier_id.name, str(res['tracking_number']), self.carrier_price, order_currency.name)
            order.message_post(body=msg)'''


