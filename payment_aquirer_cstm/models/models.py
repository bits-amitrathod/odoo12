# -*- coding: utf-8 -*-

from odoo import models, fields, api

class payment_aquirer_cstm(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('purchaseorder', 'Purchase Order')])
    @api.multi
    def purchaseorder_get_form_action_url(self):
        self.ensure_one()
        return "/shop/payment/purchaseorderform"


class SalesOrderDeliveryMethod(models.Model):
    _inherit = "sale.order"

    expedited_shipping = fields.Text('Expedited Shipping')