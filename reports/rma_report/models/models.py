# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime

_logger = logging.getLogger(__name__)
class rma_report(models.Model):
    _inherit = 'stock.picking'

    customer = fields.Char("Customer", store=False, compute="_calculate")
    created= fields.Char("Created", store=False)
    status = fields.Char("Status", store=False)
    qty = fields.Integer('Qty', store=False)
    product=fields.Char("Product", store=False)
    # ph=fields.Char("Phone", store=False)
    # email=fields.Char("Email", store=False)

    @api.multi
    def _calculate(self):

        for order in self:
            order.customer = order.partner_id.display_name
            order.created=order.scheduled_date
            order.status=order.state
            # order.qty = order.quantity
            # order.product=
            # order.ph=order.product_id.product_tmpl_id.product_brand_id.partner_id.phone
            # order.email = order.product_id.product_tmpl_id.product_brand_id.partner_id.email
            # for p in order.quant_ids:
            #     order.p_qty = p.quantity
