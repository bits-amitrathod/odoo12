# -*- coding: utf-8 -*-

from odoo import models, fields, api

class payment_aquirer_cstm(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('purchaseorder', 'Purchase Order')
    ], ondelete={'purchaseorder': 'set default'})

    #@api.multi
    def purchaseorder_get_form_action_url(self):
        self.ensure_one()
        return "/shop/payment/purchaseorderform"


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    def _check_carrier_quotation(self, force_carrier_id=None):
        self.ensure_one()
        DeliveryCarrier = self.env['delivery.carrier']

        if self.only_services:
            self.write({'carrier_id': None})
            self._remove_delivery_line()
            return True
        else:
            self = self.with_company(self.company_id)
            # attempt to use partner's preferred carrier
            if not force_carrier_id and self.partner_shipping_id.property_delivery_carrier_id:
                force_carrier_id = self.partner_shipping_id.property_delivery_carrier_id.id

            carrier = force_carrier_id and DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
            available_carriers = self._get_delivery_methods()
            if carrier:
                if carrier not in available_carriers:
                    carrier = DeliveryCarrier
                else:
                    # set the forced carrier at the beginning of the list to be verfied first below
                    available_carriers -= carrier
                    available_carriers = carrier + available_carriers
            if force_carrier_id or not carrier or carrier not in available_carriers:
                verified_carrier = False
                for delivery in available_carriers:
                    if delivery.code == "my_shipper_account":
                        if self.partner_id.having_carrier and self.partner_id.carrier_acc_no:
                            verified_carrier = delivery._match_address(self.partner_shipping_id)
                    else:
                        verified_carrier = delivery._match_address(self.partner_shipping_id)
                    if verified_carrier:
                        carrier = delivery
                        break
                self.write({'carrier_id': carrier.id})
            self._remove_delivery_line()
            if carrier:
                res = carrier.rate_shipment(self)
                if res.get('success'):
                    self.set_delivery_line(carrier, res['price'])
                    self.delivery_rating_success = True
                    self.delivery_message = res['warning_message']
                else:
                    self.set_delivery_line(carrier, 0.0)
                    self.delivery_rating_success = False
                    self.delivery_message = res['error_message']

        return bool(carrier)

