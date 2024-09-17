# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return APS-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values of the transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'purchaseorder':
            return res

        converted_amount = payment_utils.to_minor_currency_units(self.amount, self.currency_id)
        base_url = self.provider_id.get_base_url()
        rendering_values = {
            'command': 'PURCHASE',
            'amount': str(converted_amount),
            'currency': self.currency_id.name,
            'language': self.partner_lang[:2] if self.partner_lang else 'en_US',
            'customer_email': self.partner_id.email_normalized,
            'return_url': urls.url_join(base_url, '/shop'),
            'api_url': self.provider_id._purchaseorder_get_api_url(),
            'tx_id': self.id,
        }
        return rendering_values