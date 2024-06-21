# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class SalePayLink(models.Model):
    _name = "sale.pay.link.cust"

    allow_pay_gen_payment_link = fields.Boolean("Allow Pay")
    sale_order_id = fields.Integer()
    invoice_id = fields.Integer()