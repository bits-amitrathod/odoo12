from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    price_reduce = fields.Float(string='Final Price', digits='Product Price',
                                readonly=True)
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        sale_orders = self.env['sale.order'].search([('name', '=', partner.sale_order)], limit=1)
        l = [line for line in sale_orders.order_line if
             line.product_id.id == product.id and line.discount == discount] if sale_orders else False
        price = l[0].price_reduce if sale_orders and l and l[0] else False

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        if move_type == 'out_invoice' or move_type == 'out_refund':  # this is customized for SO # this is customized for SO
            if self.sale_line_ids:
                so_price_unit = self.sale_line_ids[0].price_reduce
                difference = line_discount_price_unit - so_price_unit
                if (round(abs(difference), 2) <= 0.01):
                    line_discount_price_unit = so_price_unit

            elif price:
                difference = line_discount_price_unit - price
                if (round(abs(difference), 2) <= 0.01):
                    line_discount_price_unit = price
            else:
                line_discount_price_unit = round(price_unit * (1 - (discount / 100.0)), 2)
        subtotal = quantity * line_discount_price_unit

        res['price_reduce'] = line_discount_price_unit
        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                                                                             quantity=quantity, currency=currency,
                                                                             product=product, partner=partner,
                                                                             is_refund=move_type in (
                                                                                 'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        lines = super(AccountMoveLine, self).create(vals_list)
        for line in lines:
            if line.sale_line_ids:
                line.price_unit = line.sale_line_ids[0].price_unit
                line.price_reduce = line.sale_line_ids[0].price_reduce

        return lines
