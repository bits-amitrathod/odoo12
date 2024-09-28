from odoo import api, fields, models ,_
import datetime
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrderPopUp(models.TransientModel):
    _name = 'purchase.order.shipping.popup'
    _description = "Purchase Order PopUp"

    def _get_default_carrier(self):
        active_model  = self._context.get('active_model')
        active_id  = self._context.get('active_id')
        if active_model and active_id:
            purchase_order = self.env[active_model].sudo().browse(int(active_id))
            carrier = purchase_order.carrier_id

        carrier = carrier or self.env['delivery.carrier'].with_context({'active_test':False}).search([('name', '=', 'Vendor_Fedex Ground')])
        if carrier:
            return carrier.id

    def _get_default_packaging(self):
        packing = self.env['stock.package.type'].search([('name', '=', 'FEDEX_YOUR_PACKAGING')], limit=1)
        if packing:
            return packing.id

    def _get_default_weight(self):
        order = self.env['purchase.order'].browse(self._context['active_id'])
        val = 0
        for obj in order.order_line:
            val = val+obj.product_id.weight
        if val == 0:
            val = 5.00
        return val

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', required=True, ondelete='cascade',
                                 domain="[('delivery_type','=','fedex')]", default=_get_default_carrier)

    product_packaging = fields.Many2one('stock.package.type', string='Package', domain="[('package_carrier_type','=','fedex')]", default=_get_default_packaging)

    weight = fields.Float('Weight', default=_get_default_weight)
    package_count = fields.Integer("Packages Count", default=1)

    @api.constrains('package_count')
    #@api.one
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


