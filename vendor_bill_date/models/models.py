from odoo import models, fields, api
from odoo import api, fields, models, _
from datetime import timedelta

class VendorBillDate(models.Model):
    _inherit ='account.move'

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        for invoice in self:
            # Dispatch lines and pre-compute some aggregated values like taxes.
            for line in invoice.line_ids:
                if line.recompute_tax_line:
                    recompute_all_taxes = True
                    line.recompute_tax_line = False

            # Compute taxes.
            if recompute_all_taxes:
                invoice._recompute_tax_lines()
            if recompute_tax_base_amount:
                invoice._recompute_tax_lines(recompute_tax_base_amount=True)

            if invoice.is_invoice(include_receipts=True):
                # Compute cash rounding.
                invoice._recompute_cash_rounding_lines()

                # Compute payment terms.
                invoice._recompute_payment_terms_lines()

                # Only synchronize one2many in onchange.
                if invoice != invoice._origin:
                    invoice.invoice_line_ids = invoice.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)

                if not invoice.invoice_date:
                    today = fields.Date.context_today(self)
                    if self.invoice_payment_term_id:
                        self.invoice_date = today
                    else:
                        self.invoice_date = self.invoice_date_due or self.invoice_date or today


    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        # super(VendorBillDate,self). _onchange_payment_term_date_invoice()
        stock_picking_obj = False
        # add_hrs = None

        if self.origin:
            if self.type == "in_invoice":
                # Populates Bill_Date on pageload (onchange()) at the time of creating bill of purchase_order in Purchase module
                stock_picking_obj = self.env['stock.picking'].search([('origin', '=', self.origin), ('state', '=', 'done')])
                # add_hrs = 6

            elif self.type == "out_invoice":
                # Populates Invoice_Date on pageload (onchange()) at the time of creating invoice of sale_order in Sale module
                stock_picking_obj = self.env['stock.picking'].search( [('origin', '=', self.origin), ('state', '=', 'done'), ('picking_type_id', '=', 5)])
                # add_hrs = 5


            if not self.date_invoice:
                self.date_invoice = str((max(stock_picking_obj).date_done)) if stock_picking_obj else None # + timedelta(hours=add_hrs)).date(

        # Setting due_date according to current(updated) invoice_date (not according to current date)

        if self.payment_term_id:
            pterm = self.payment_term_id
            pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=self.date_invoice)[0]
            self.date_due = max(line[0] for line in pterm_list)

        elif self.date_due: #and (self.date_invoice > self.date_due):
            if self.date_invoice > self.date_due:
                self.date_due = self.date_invoice

    # @api.multi
    def action_date_assign(self):
        for inv in self:
            # Here the onchange will automatically write to the database
            inv._onchange_payment_term_date_invoice()
        return True


    # Populates Due_Date at the time of Saving bill of purchase order in Purchase module when click on 'Save' button
    # def create(self, vals):
    #     ret_invoice=super(VendorBillDate,self).create(vals)
    #     ret_invoice.action_date_assign()
    #     return ret_invoice

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

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
        if move_type == 'out_invoice':  # this is customized for SO
            if self.sale_line_ids:
                so_price_unit = self.sale_line_ids[0].price_reduce
                difference = line_discount_price_unit - so_price_unit
                if (round(abs(difference), 2) <= 0.5):
                    line_discount_price_unit = so_price_unit

            elif price:
                difference = line_discount_price_unit - price
                if (round(abs(difference), 2) <= 0.5):
                    line_discount_price_unit = price
            else:
                line_discount_price_unit = round(price_unit * (1 - (discount / 100.0)), 2)
        subtotal = quantity * line_discount_price_unit

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
    def create(self, vals_list):
        # OVERRIDE
        lines = super(AccountMoveLine, self).create(vals_list)
        for line in lines:
            if line.sale_line_ids:
                line.price_unit = line.sale_line_ids[0].price_unit

        return lines
class Memo(models.Model):
    # Via this inherited model, handled an xml condition
    _inherit = "account.payment"
