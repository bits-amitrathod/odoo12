
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _order = 'req_no ASC'

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Business Development', readonly=True)

    product_min_max_exp_date = fields.Char('Product Min-Max Expiration Date',
                                           compute='_calculate_max_min_lot_expiration')

    def _calculate_max_min_lot_expiration(self):
        for record in self:
            if record.product_id and record.product_id.id:
                for picking_id in record.order_id.picking_ids:
                    if picking_id.picking_type_id.id == 1 and picking_id.state != 'cancel':
                        for move_line in picking_id.move_line_ids:
                            if move_line.state != 'cancel':
                                if record.product_id.id == move_line.product_id.id:
                                    self.env.cr.execute(
                                        """
                                        SELECT
                                        sum(quantity), min(use_date), max(use_date)
                                        FROM
                                            stock_quant
                                        INNER JOIN
                                            stock_lot
                                        ON
                                            (
                                                stock_quant.lot_id = stock_lot.id)
                                        INNER JOIN
                                            stock_location
                                        ON
                                            (
                                                stock_quant.location_id = stock_location.id)
                                        WHERE
                                            stock_location.usage in('internal', 'transit') and stock_lot.product_id  = %s and
                                            stock_lot.id in (select lot_id from public.stock_move_line sml where move_id = %s )
                                            """, (move_line.product_id.id, move_line.id))
                                    query_result = self.env.cr.dictfetchone()
                                    if query_result['min'] is not None and query_result['max'] is not None and \
                                            query_result['min'] == query_result['max']:
                                        record.product_min_max_exp_date = str(
                                            datetime.datetime.strptime(str(query_result['min']),
                                                                       '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'))
                                    elif query_result['min'] is not None and query_result['max'] is not None and \
                                            query_result['min'] and query_result['max']:
                                        record.product_min_max_exp_date = str(datetime.datetime.strptime(str(query_result['min']), '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')) \
                                            + str("-") + str(datetime.datetime.strptime(str(query_result['max']), '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'))
                                    else:
                                        record.product_min_max_exp_date = None
                                else:
                                    if record.product_min_max_exp_date:
                                        record.product_min_max_exp_date = record.product_min_max_exp_date
                                    else:
                                        record.product_min_max_exp_date = None
                            else:
                                record.product_min_max_exp_date = None
                    else:
                        record.product_min_max_exp_date = None

    def unlink(self):
        if self.filtered(lambda line: line.state in ('sale', 'done') and (line.invoice_lines or not line.is_downpayment)):
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        elif self.filtered(lambda line: line.order_id.team_id.team_type == 'engine' and (line.state in ('sent', 'sale', 'done') and (line.invoice_lines or not line.is_downpayment))):
            raise UserError(_('You can not remove an order line.\nYou should rather set the quantity to 0.'))

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
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            else:
                product_currency = product_currency or (product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id

            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    def _get_display_price_custom(self, pricelist , product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
            )

        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id, uom=self.product_uom.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule_custom_web(pricelist, product or self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency != self.order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.pricelist_id.currency_id,
                self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)


class PricelistCustomWeb(models.Model):
    _inherit = "product.pricelist"

    def get_product_price_rule_custom_web(self, pricelist, product, quantity, partner, date=False, uom_id=False):
        """ For a given pricelist, return price and rule for a given product """
        return pricelist._compute_price_rule(product, quantity, uom=uom_id, date=date)[product.id]

class ProductTemplateCustomWeb(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):

        combination_info = super(ProductTemplateCustomWeb, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        product_template = self
        combination = combination or product_template.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = product_template._get_first_possible_combination(parent_combination)

        if only_template:
            product = product_template.env['product.product']
        elif product_id and not combination:
            product = product_template.env['product.product'].browse(product_id)
        else:
            product = product_template._get_variant_for_combination(combination)

        test_price_unit = combination_info['list_price']
        if pricelist and product:
            test_price_unit = self.env['account.tax']._fix_tax_included_price_company(
                self.env['sale.order.line']._get_display_price_custom(pricelist, product), product.taxes_id,
                self.env['account.tax'], self.env['sale.order'].company_id)

        combination_info.update({
            'list_price_custom': test_price_unit,
        })
        return combination_info



