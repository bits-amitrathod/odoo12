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

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            currency = line.order_id.company_id.currency_id
            if line.product_uom.name == 'Each':
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            else:
                if line.product_uom.factor_inv > 0:
                    price = currency.round((line.price_unit / line.product_uom.factor_inv)
                                           * (1.0 - (line.discount or 0.0) / 100.0)) * line.product_uom.factor_inv
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            # price2 = line.price_reduce * (1 - (line.discount or 0.0) / 100.0)
            price_subtotal = line.product_uom_qty * line.price_reduce
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': price_subtotal,
            })
            if line.price_reduce != line.price_unit and line.discount == 0:
                line.update({'price_unit': price})

    @api.depends('price_unit', 'discount')
    def _get_price_reduce(self):
        for line in self:
            fixed_price = False
            for x in line.order_id.pricelist_id.item_ids:
                if x.compute_price == 'fixed' and x.applied_on in ['1_product', '0_product_variant']:
                    if x.applied_on in ['1_product']:
                        if line.product_id.product_tmpl_id.id == x.product_tmpl_id.id:
                            fixed_price = x.fixed_price
                    if x.applied_on in ['0_product_variant']:
                        if line.product_id.product_tmpl_id.id == x.product_id.id:
                            fixed_price = x.fixed_price

            currency = line.order_id.company_id.currency_id
            if line.product_uom.name == 'Each':
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            else:
                if line.product_uom.factor_inv > 0:
                    price_reduce = currency.round((line.price_unit / line.product_uom.factor_inv)
                                                  * (1.0 - line.discount / 100.0)) * line.product_uom.factor_inv
            if fixed_price:
                if abs(fixed_price - price_reduce) >= 0.5:
                    line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                else:
                    line.price_reduce = fixed_price
            else:
                if line.product_uom.name == 'Each':
                    line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                else:
                    if line.product_uom.factor_inv > 0:
                        line.price_reduce = currency.round((line.price_unit / line.product_uom.factor_inv)
                                                           * (1.0 - line.discount / 100.0)) \
                                            * line.product_uom.factor_inv

class SaleOrderCstm(models.Model):
    _inherit = "sale.order"

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