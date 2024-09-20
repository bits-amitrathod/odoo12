# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.tools import float_is_zero, float_repr
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

_logger = logging.getLogger(__name__)


class apprisal_tracker_vendor(models.Model):

    _inherit = "purchase.order"

    tier1_extra_retail = fields.Monetary(string="Tier 1 Extra Retail", tracking=True)
    tier2_extra_retail = fields.Monetary(string="Tier 2 Extra Retail", tracking=True)
    less_than_40_extra_retail = fields.Monetary(string="< 40% Extra Retail", tracking=True)

    tier1_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 1 Retail")
    tier2_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 2 Retail")
    less_than_40_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="< 40% Retail")
    broker_margin = fields.Char(compute="_value_broker_margin", store=False)
    cust_type_appraisal = fields.Char(compute="_value_broker_margin", store=False,string="Type")

    tier1_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 1 Margin")
    tier2_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 2 Margin")
    less_than_40_margin = fields.Char(compute="_value_broker_margin", store=False, string="< 40% Margin")

    status_ven_app = fields.Char(string="Status",store=False)
    vendor_cust_id_app = fields.Char(string="Customer ID", store=False ,compute="_value_broker_margin")

    @api.onchange('broker_margin')
    def _value_broker_margin(self):

            for order in self:
                order.broker_margin=None

                order.status_ven_app = order.status_ven
                order.vendor_cust_id_app = order.partner_id.saleforce_ac
                if order.state in ('ven_draft', 'ven_sent'):
                    order.status_ven_app = 'Vendor Offer'

                if order.state == 'purchase':
                    order.status_ven_app = 'Accepted'

                if order.arrival_date_grp and order.arrival_date_grp != '':
                    order.status_ven_app = 'Arrived'

                order_list = self.env['stock.picking'].search([('purchase_id', '=', order.id)])
                for order1 in order_list:
                    if order1.date_done and order1.date_done != '':
                        order.status_ven_app = 'Checked Into Inventory'

                if order.invoice_status and order.invoice_status == 'invoiced':
                    order.status_ven_app = 'Bill created'

                if order.state == 'cancel':
                    order.status_ven_app = 'Declined'

                # account_invoice = self.env['account.invoice'].search([('origin', '=', order.name)])
                # for acc in account_invoice:
                #     if acc.number:
                #         account_payment = self.env['account.payment'].search([('communication', '=', acc.number)])
                #         for acc_p in account_payment:
                #             if acc_p.state and acc_p.state == 'sent':
                #                 order.status_ven_app = 'Check Sent'

                tier1_retail_temp = 0
                tier2_retail_temp = 0
                less_than_40_retail = 0

                if order.partner_id.is_wholesaler:

                    order.cust_type_appraisal = 'Wholesaler'
                    for line in order.order_line:
                        if line.product_unit_price and line.product_unit_price > 0:
                            amt = line.product_offer_price / line.product_unit_price

                            if (line.product_id.tier.code == '1') and \
                                    (abs(float(amt - 1)) >= 0.48):
                                tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price

                            if (((line.product_id.tier.code == '1') and \
                                 ((abs(float(amt - 1)) >= 0.4) and (abs(float(amt - 1)) < 0.48)))
                                    or (line.product_id.tier.code == '2' and (abs(float(amt-1)) >= 0.4))
                            ):
                                tier2_retail_temp = tier2_retail_temp + line.billed_product_retail_price

                            if abs(float(amt - 1)) < 0.4:
                                less_than_40_retail = less_than_40_retail + line.billed_product_retail_price

                    tier1_retail_temp = tier1_retail_temp + order.tier1_extra_retail
                    tier2_retail_temp = tier2_retail_temp + order.tier2_extra_retail
                    less_than_40_retail = less_than_40_retail + order.less_than_40_extra_retail

                    order.update({
                        'tier1_retail': tier1_retail_temp,
                        'tier2_retail': tier2_retail_temp,
                        'less_than_40_retail': less_than_40_retail
                    })

                elif order.partner_id.is_broker:

                    order.cust_type_appraisal = 'Broker'

                    for line in order.order_line:
                        if line.product_id.tier.code == '1':
                            tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price
                        if line.product_id.tier.code == '2':
                            tier2_retail_temp = tier2_retail_temp + line.billed_product_retail_price

                    tier1_retail_temp = tier1_retail_temp + order.tier1_extra_retail
                    tier2_retail_temp = tier2_retail_temp + order.tier2_extra_retail
                    less_than_40_retail = less_than_40_retail + order.less_than_40_extra_retail

                    order.update({
                        'tier1_retail': tier1_retail_temp,
                        'tier2_retail': tier2_retail_temp,
                        'less_than_40_retail': less_than_40_retail
                    })

                elif order.partner_id.charity:
                    order.cust_type_appraisal = 'Charity'

                    for line in order.order_line:
                        if line.product_id.tier.code == '1':
                            tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price
                        if line.product_id.tier.code == '2':
                            tier2_retail_temp = tier2_retail_temp + line.billed_product_retail_price

                    tier1_retail_temp = tier1_retail_temp + order.tier1_extra_retail
                    tier2_retail_temp = tier2_retail_temp + order.tier2_extra_retail
                    less_than_40_retail = less_than_40_retail + order.less_than_40_extra_retail

                    order.update({
                        'tier1_retail': tier1_retail_temp,
                        'tier2_retail': tier2_retail_temp,
                        'less_than_40_retail': less_than_40_retail
                    })

                else:
                    order.cust_type_appraisal = 'Traditional'
                    for line in order.order_line:
                        if line.product_id.tier.code == '1':
                            tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price
                        if line.product_id.tier.code == '2':
                            tier2_retail_temp = tier2_retail_temp + line.billed_product_retail_price

                    tier1_retail_temp = tier1_retail_temp + order.tier1_extra_retail
                    tier2_retail_temp = tier2_retail_temp + order.tier2_extra_retail
                    less_than_40_retail = less_than_40_retail + order.less_than_40_extra_retail

                    order.update({
                        'tier1_retail': tier1_retail_temp,
                        'tier2_retail': tier2_retail_temp,
                        'less_than_40_retail': less_than_40_retail
                    })

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            line_item_present = False
            price_subtotal_all = 0
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    line_item_present = True
                    price_subtotal_all += line.price_subtotal
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            if line_item_present and self.offer_type and self.offer_type == 'credit':
                credit_amount = self.amount_total-price_subtotal_all
                invoice_vals['invoice_line_ids'].append((0, 0, self.add_credit_line_item_in_PO(credit_amount)))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            if self.effective_date:
                vals['invoice_date']= self.effective_date
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)

    def add_credit_line_item_in_PO(self, credit_amount, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        account_id = self.env['account.account'].search([('code', '=', '50007'),
                                                         ('company_id', '=', self.company_id.id)], limit=1)
        res = {
            'sequence': 1,
            'name': 'CREDIT (%s - %s)' % (self.name, self.appraisal_no),
            'quantity': 1,
            'price_unit': credit_amount,
            'account_id': account_id.id
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id
        })
        return res


class CustomerAsWholesaler(models.Model):
    _inherit = 'res.partner'

    is_wholesaler = fields.Boolean(string="Is a Wholesaler?")

    @api.onchange('is_wholesaler', 'is_broker', 'charity')
    def _check_wholesaler_setting(self):
        warning = {}
        val = {}
        if self.is_broker is True and (self.is_wholesaler is True or self.charity is True):
            val.update({'is_broker': False})
            if self.is_wholesaler is True and self.charity is True:
                val.update({'is_wholesaler': False})
            warning = {
                'title': _('Warning'),
                'message': _('Customer can be Wholesaler or Broker or Charity'),
            }
        elif self.is_wholesaler is True and self.charity is True:
            val.update({'is_wholesaler': False})
            warning = {
                'title': _('Warning'),
                'message': _('Customer can be Wholesaler or Broker or Charity'),
            }
        return {'value': val, 'warning': warning}


class ApprisalTrackerExport(models.TransientModel):
    _name = 'appraisaltracker.export'
    _description = 'appraisaltracker.export'

    def download_excel_appraisal_tracker(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/export/appraisal_xl',
            'target': 'new'
        }




class ProductProduct(models.Model):
    _inherit = 'product.product'


    # def _compute_average_price(self, qty_invoiced, qty_to_invoice, stock_moves, is_returned=False):
    #     """Go over the valuation layers of `stock_moves` to value `qty_to_invoice` while taking
    #     care of ignoring `qty_invoiced`. If `qty_to_invoice` is greater than what's possible to
    #     value with the valuation layers, use the product's standard price.
    #
    #     :param qty_invoiced: quantity already invoiced
    #     :param qty_to_invoice: quantity to invoice
    #     :param stock_moves: recordset of `stock.move`
    #     :returns: the anglo saxon price unit
    #     :rtype: float
    #     """
    #     try:
    #         self.ensure_one()
    #         if not qty_to_invoice:
    #             return 0.0
    #
    #         returned_quantities = defaultdict(float)
    #         for move in stock_moves:
    #             if move.origin_returned_move_id:
    #                 returned_quantities[move.origin_returned_move_id.id] += abs(sum(move.stock_valuation_layer_ids.mapped('quantity')))
    #         candidates = stock_moves\
    #             .sudo()\
    #             .filtered(lambda m: not (m.origin_returned_move_id and sum(m.stock_valuation_layer_ids.mapped('quantity')) >= 0))\
    #             .mapped('stock_valuation_layer_ids')\
    #             .sorted()
    #         qty_to_take_on_candidates = qty_to_invoice
    #         tmp_value = 0  # to accumulate the value taken on the candidates
    #         for candidate in candidates:
    #
    #             logging.error("=========== ============= candidate")
    #             logging.error(candidate.id)
    #             candidate_quantity = abs(candidate.quantity)
    #             if candidate.stock_move_id.id in returned_quantities:
    #                 candidate_quantity -= returned_quantities[candidate.stock_move_id.id]
    #             if float_is_zero(candidate_quantity, precision_rounding=candidate.uom_id.rounding):
    #                 continue  # correction entries
    #             if not float_is_zero(qty_invoiced, precision_rounding=candidate.uom_id.rounding):
    #                 qty_ignored = min(qty_invoiced, candidate_quantity)
    #                 qty_invoiced -= qty_ignored
    #                 candidate_quantity -= qty_ignored
    #                 if float_is_zero(candidate_quantity, precision_rounding=candidate.uom_id.rounding):
    #                     continue
    #             qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate_quantity)
    #
    #             qty_to_take_on_candidates -= qty_taken_on_candidate
    #             logging.error("=========== ============= candidate.quantity")
    #             logging.error(candidate.quantity)
    #             tmp_value += qty_taken_on_candidate * \
    #                 ((candidate.value + sum(candidate.stock_valuation_layer_ids.mapped('value'))) / candidate.quantity)
    #             if float_is_zero(qty_to_take_on_candidates, precision_rounding=candidate.uom_id.rounding):
    #                 break
    #
    #         # If there's still quantity to invoice but we're out of candidates, we chose the standard
    #         # price to estimate the anglo saxon price unit.
    #         if not float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
    #             negative_stock_value = self.standard_price * qty_to_take_on_candidates
    #             tmp_value += negative_stock_value
    #
    #         return tmp_value / qty_to_invoice
    #
    #     except Exception as e:
    #         logging.error("prod issue po \n Exception12: %s" % str(e))