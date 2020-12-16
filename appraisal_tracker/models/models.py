# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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

    color = fields.Integer(compute="_value_broker_margin", store=False)

    t1color = fields.Integer(compute="_value_broker_margin", store=False)
    t2color = fields.Integer(compute="_value_broker_margin", store=False)
    lscolor = fields.Integer(compute="_value_broker_margin", store=False)

    status_ven_app = fields.Char(string="Status",store=False)
    vendor_cust_id_app = fields.Char(string="Customer ID", store=False ,compute="_value_broker_margin")

    @api.onchange('broker_margin')
    def _value_broker_margin(self):

            for order in self:

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

                account_invoice = self.env['account.invoice'].search([('origin', '=', order.name)])
                for acc in account_invoice:
                    if acc.number:
                        account_payment = self.env['account.payment'].search([('communication', '=', acc.number)])
                        for acc_p in account_payment:
                            if acc_p.state and acc_p.state == 'sent':
                                order.status_ven_app = 'Check Sent'

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
                                    or (line.product_id.tier.code == '2' and (abs(float(amt-1)) > 0.4))
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
                        if line.product_unit_price and line.product_unit_price > 0:
                            amt = line.product_offer_price/line.product_unit_price

                            if (line.product_id.tier.code == '1') and \
                                    (abs(float(amt - 1)) >= 0.48):

                                tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price

                            if (((line.product_id.tier.code == '1') and \
                                    ((abs(float(amt - 1)) >= 0.4) and (abs(float(amt - 1)) < 0.48)))
                                    or (line.product_id.tier.code == '2' and (abs(float(amt-1)) > 0.4))
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

                elif order.partner_id.charity:

                    order.cust_type_appraisal = 'Charity'

                    for line in order.order_line:
                        if line.product_unit_price and line.product_unit_price > 0:
                            amt = line.product_offer_price/line.product_unit_price

                            if (line.product_id.tier.code == '1') and \
                                    (abs(float(amt - 1)) >= 0.48):

                                tier1_retail_temp = tier1_retail_temp + line.billed_product_retail_price

                            if (((line.product_id.tier.code == '1') and \
                                    ((abs(float(amt - 1)) >= 0.4) and (abs(float(amt - 1)) < 0.48)))
                                    or (line.product_id.tier.code == '2' and (abs(float(amt-1)) > 0.4))
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





