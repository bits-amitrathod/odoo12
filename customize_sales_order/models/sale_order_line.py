
from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    # @api.multi
    # def unlink(self):
    #     if self.filtered(lambda line: line.state in 'done' and (line.invoice_lines or not line.is_downpayment)):
    #         raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
    #     return models.Model.unlink(self)

    @api.multi
    def unlink(self):
        if self.filtered(
                lambda line: line.state in ('sale', 'done') and (line.invoice_lines or not line.is_downpayment)):
            raise UserError(_(
                'You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        elif self.filtered(
                lambda line: line.order_id.team_id.team_type == 'engine' and
                             (line.state in ('sent', 'sale', 'done') and (line.invoice_lines or not line.is_downpayment))):
            raise UserError(_(
                'You can not remove an order line.\nYou should rather set the quantity to 0.'))

        return super(SaleOrderLineInherit, self).unlink()

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # When modifying a one2many, _origin doesn't guarantee that its values will be the ones
        # in database. Hence, we need to explicitly read them from there.
        if self._origin:
            product_uom_qty_origin = self._origin.read(["product_uom_qty"])[0]["product_uom_qty"]
        else:
            product_uom_qty_origin = 0

        if self.state == 'sale' and self.product_id.type in ['product',
                                                             'consu'] and self.product_uom_qty < product_uom_qty_origin:
            # Do not display this warning if the new quantity is below the delivered
            # one; the `write` will raise an `UserError` anyway.
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _(
                    'You are decreasing the ordered quantity! Do not forget to manually update the delivery order if needed.'),
            }
            return {'warning': warning_mess}

        elif self.order_id.team_id.team_type == 'engine' and (self.state in ('sale', 'sent') and self.product_id.type in ['product',
                                                             'consu'] and self.product_uom_qty < product_uom_qty_origin):
            # Do not display this warning if the new quantity is below the delivered
            # one; the `write` will raise an `UserError` anyway.
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _(
                    'You are decreasing the ordered quantity! Do not forget to manually update the delivery order if needed.'),
            }
            return {'warning': warning_mess}
        return {}

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

            product_currency = product_currency or (
                        product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.user.company_id, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id