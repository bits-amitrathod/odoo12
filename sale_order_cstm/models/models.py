# -*- coding: utf-8 -*-

from odoo import models, fields,api, _
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
            self.product_id.product_tmpl_id._compute_quantities()
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.actual_quantity, product_qty, precision_digits=precision) == -1:
                message = _('You plan to sell %s %s but you only have %s %s available ') % \
                          (self.product_uom_qty, self.product_uom.name, product.actual_quantity, product.uom_id.name)

                warning_mess = {
                    'title': _('Not enough inventory!'),
                    'message': message
                }
                return {'warning': warning_mess}
        return {}

class SaleOrderCstm(models.Model):
    _inherit = "sale.order"

    allow_pay_gen_payment_link = fields.Boolean("Allow Pay")

    def get_email_so_sendByEmail(self):
        self.ensure_one()
        user_id_email = None
        customer = self.partner_id.parent_id if self.partner_id.parent_id else self.partner_id
        if customer.account_manager_cust:
            user_id_email = customer.account_manager_cust
        elif customer.user_id:
            if customer.user_id.name == "National Accounts" and customer.national_account_rep:
                user_id_email = customer.national_account_rep
            else:
                user_id_email = customer.user_id
        elif customer.national_account_rep:
            user_id_email = customer.national_account_rep
        else:
            user_id_email = customer.user_id

        return user_id_email