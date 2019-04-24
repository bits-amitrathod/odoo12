# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.tools.float_utils import float_compare


class SaleOrderAvailability(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            total_available = product.qty_available - product.outgoing_qty
            if float_compare(total_available, product_qty, precision_digits=precision) == -1:
                message = _('You plan to sell %s %s but you only have %s %s available ') % \
                          (self.product_uom_qty, self.product_uom.name, total_available, product.uom_id.name)

                warning_mess = {
                    'title': _('Not enough inventory!'),
                    'message': message
                }
                return {'warning': warning_mess}
        return {}
