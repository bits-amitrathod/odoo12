# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from collections import defaultdict
from odoo.tools import float_is_zero, float_repr

_logger = logging.getLogger(__name__)


class apprisal_tracker_vendor(models.Model):

    _inherit = "purchase.order"

    tier1_extra_retail = fields.Monetary(string="Tier 1 Extra Retail", track_visibility='onchange')
    tier2_extra_retail = fields.Monetary(string="Tier 2 Extra Retail", track_visibility='onchange')
    less_than_40_extra_retail = fields.Monetary(string="< 40% Extra Retail", track_visibility='onchange')

    tier1_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 1 Retail")
    tier2_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 2 Retail")
    less_than_40_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="< 40% Retail")
    broker_margin = fields.Char(compute="_value_broker_margin", store=False)
    cust_type_appraisal = fields.Char(compute="_value_broker_margin", store=False,string="Type")

    tier1_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 1 Margin")
    tier2_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 2 Margin")
    less_than_40_margin = fields.Char(compute="_value_broker_margin", store=False, string="< 40% Margin")

    # color = fields.Integer(compute="_value_broker_margin", store=False)
    #
    # t1color = fields.Integer(compute="_value_broker_margin", store=False)
    # t2color = fields.Integer(compute="_value_broker_margin", store=False)
    # lscolor = fields.Integer(compute="_value_broker_margin", store=False)

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


    def _compute_average_price(self, qty_invoiced, qty_to_invoice, stock_moves):
        """Go over the valuation layers of `stock_moves` to value `qty_to_invoice` while taking
        care of ignoring `qty_invoiced`. If `qty_to_invoice` is greater than what's possible to
        value with the valuation layers, use the product's standard price.

        :param qty_invoiced: quantity already invoiced
        :param qty_to_invoice: quantity to invoice
        :param stock_moves: recordset of `stock.move`
        :returns: the anglo saxon price unit
        :rtype: float
        """
        try:
            self.ensure_one()
            if not qty_to_invoice:
                return 0.0

            returned_quantities = defaultdict(float)
            for move in stock_moves:
                if move.origin_returned_move_id:
                    returned_quantities[move.origin_returned_move_id.id] += abs(sum(move.stock_valuation_layer_ids.mapped('quantity')))
            candidates = stock_moves\
                .sudo()\
                .filtered(lambda m: not (m.origin_returned_move_id and sum(m.stock_valuation_layer_ids.mapped('quantity')) >= 0))\
                .mapped('stock_valuation_layer_ids')\
                .sorted()
            qty_to_take_on_candidates = qty_to_invoice
            tmp_value = 0  # to accumulate the value taken on the candidates
            for candidate in candidates:
                
                logging.error("=========== ============= candidate")
                logging.error(candidate.id)
                candidate_quantity = abs(candidate.quantity)
                if candidate.stock_move_id.id in returned_quantities:
                    candidate_quantity -= returned_quantities[candidate.stock_move_id.id]
                if float_is_zero(candidate_quantity, precision_rounding=candidate.uom_id.rounding):
                    continue  # correction entries
                if not float_is_zero(qty_invoiced, precision_rounding=candidate.uom_id.rounding):
                    qty_ignored = min(qty_invoiced, candidate_quantity)
                    qty_invoiced -= qty_ignored
                    candidate_quantity -= qty_ignored
                    if float_is_zero(candidate_quantity, precision_rounding=candidate.uom_id.rounding):
                        continue
                qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate_quantity)

                qty_to_take_on_candidates -= qty_taken_on_candidate
                logging.error("=========== ============= candidate.quantity")
                logging.error(candidate.quantity)
                tmp_value += qty_taken_on_candidate * \
                    ((candidate.value + sum(candidate.stock_valuation_layer_ids.mapped('value'))) / candidate.quantity)
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=candidate.uom_id.rounding):
                    break

            # If there's still quantity to invoice but we're out of candidates, we chose the standard
            # price to estimate the anglo saxon price unit.
            if not float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                negative_stock_value = self.standard_price * qty_to_take_on_candidates
                tmp_value += negative_stock_value

            return tmp_value / qty_to_invoice

        except Exception as e:
            logging.error("prod issue po \n Exception12: %s" % str(e))


    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        self.ensure_one()
        if 1 == 1:
            return
        if company is None:
            company = self.env.company
        svls_to_vacuum = self.env['stock.valuation.layer'].sudo().search([
            ('product_id', '=', self.id),
            ('remaining_qty', '<', 0),
            ('stock_move_id', '!=', False),
            ('company_id', '=', company.id),
        ], order='create_date, id')
        if not svls_to_vacuum:
            return

        domain = [
            ('company_id', '=', company.id),
            ('product_id', '=', self.id),
            ('remaining_qty', '>', 0),
            ('create_date', '>=', svls_to_vacuum[0].create_date),
        ]
        all_candidates = self.env['stock.valuation.layer'].sudo().search(domain)

        for svl_to_vacuum in svls_to_vacuum:
            # We don't use search to avoid executing _flush_search and to decrease interaction with DB
            candidates = all_candidates.filtered(
                lambda r: r.create_date > svl_to_vacuum.create_date
                          or r.create_date == svl_to_vacuum.create_date
                          and r.id > svl_to_vacuum.id
            )
            if not candidates:
                break
            qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
            qty_taken_on_candidates = 0
            tmp_value = 0
            for candidate in candidates:
                qty_taken_on_candidate = min(candidate.remaining_qty, qty_to_take_on_candidates)
                qty_taken_on_candidates += qty_taken_on_candidate

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value
                }
                candidate.write(candidate_vals)
                if not (candidate.remaining_qty > 0):
                    all_candidates -= candidate

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    break

            # Get the estimated value we will correct.
            remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
            new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
            corrected_value = remaining_value_before_vacuum - tmp_value
            svl_to_vacuum.write({
                'remaining_qty': new_remaining_qty,
            })

            # Don't create a layer or an accounting entry if the corrected value is zero.
            if svl_to_vacuum.currency_id.is_zero(corrected_value):
                continue

            corrected_value = svl_to_vacuum.currency_id.round(corrected_value)
            move = svl_to_vacuum.stock_move_id
            vals = {
                'product_id': self.id,
                'value': corrected_value,
                'unit_cost': 0,
                'quantity': 0,
                'remaining_qty': 0,
                'stock_move_id': move.id,
                'company_id': move.company_id.id,
                'description': 'Revaluation of %s (negative inventory)' % move.picking_id.name or move.name,
                'stock_valuation_layer_id': svl_to_vacuum.id,
            }
            vacuum_svl = self.env['stock.valuation.layer'].sudo().create(vals)

            # Create the account move.
            if self.valuation != 'real_time':
                continue
            vacuum_svl.stock_move_id._account_entry_move(
                vacuum_svl.quantity, vacuum_svl.description, vacuum_svl.id, vacuum_svl.value
            )
            # Create the related expense entry
            self._create_fifo_vacuum_anglo_saxon_expense_entry(vacuum_svl, svl_to_vacuum)

        # If some negative stock were fixed, we need to recompute the standard price.
        product = self.with_company(company.id)
        if product.cost_method == 'average' and not float_is_zero(product.quantity_svl,
                                                                  precision_rounding=self.uom_id.rounding):
            product.sudo().with_context(disable_auto_svl=True).write(
                {'standard_price': product.value_svl / product.quantity_svl})
