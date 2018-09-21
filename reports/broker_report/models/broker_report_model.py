# -*- coding: utf-8 -*-

from odoo import models, fields, api


class broker_report(models.Model):
    _inherit = 'purchase.order'

    total_retail_broker = fields.Monetary('Total Retail', store=False, compute='_compute_all_vals')
    bonus_eligible = fields.Monetary(string='Bonus Eligible', store=False)
    hospital_total = fields.Monetary(string='Hospital Total',store=False)
    broker_total = fields.Monetary('Broker Total', store=False)
    broker_greater_40_total = fields.Monetary(string='Broker > 40% Total', store=False)
    broker_less_40_total = fields.Monetary('Broker > 40% Total', store=False)
    broker_desc = fields.Char('Desc', store=False)

    total_retail_broker_tot = fields.Char('Total Retail', store=False)
    bonus_eligible_tot = fields.Char(string='Bonus Eligible', store=False)
    hospital_total_tot = fields.Char(string='Hospital Total', store=False)
    broker_total_tot = fields.Char('Broker Total', store=False)
    broker_greater_40_total_tot = fields.Char(string='Broker > 40% Total', store=False)
    broker_less_40_total_tot = fields.Char('Broker > 40% Total', store=False)
    broker_desc_tot = fields.Char('Desc', store=False)

    total_retail_broker_mar = fields.Char('Total Retail', store=False)
    bonus_eligible_mar = fields.Char(string='Bonus Eligible', store=False)
    hospital_total_mar = fields.Char(string='Hospital Total', store=False)
    broker_total_mar = fields.Char('Broker Total', store=False)
    broker_greater_40_total_mar = fields.Char(string='Broker > 40% Total', store=False)
    broker_less_40_total_mar = fields.Char('Broker > 40% Total', store=False)
    broker_desc_mar = fields.Char('Desc', store=False)


    @api.multi
    def _compute_all_vals(self):
        apprisal_list=[]
        for order in self:
            apprisal_list.append(order)
        apprisal_list_rtl_val = apprisal_list_tot_val = apprisal_list_mar_val = apprisal_list[0]
        apprisal_list_report = []
        tot_offer = 0
        margin40tot = 0
        for order in self:
            apprisal_list_rtl_val.total_retail_broker = apprisal_list_rtl_val.total_retail_broker + order.retail_amt
            apprisal_list_rtl_val.bonus_eligible = apprisal_list_rtl_val.bonus_eligible + order.bonus_eligible
            apprisal_list_rtl_val.hospital_total = apprisal_list_rtl_val.hospital_total + order.hospital_total
            apprisal_list_rtl_val.broker_total = apprisal_list_rtl_val.broker_total + order.broker_total
            apprisal_list_rtl_val.broker_greater_40_total = apprisal_list_rtl_val.broker_greater_40_total + order.broker_greater_40_total
            apprisal_list_rtl_val.broker_less_40_total = apprisal_list_rtl_val.broker_less_40_total + order.broker_less_40_total
            apprisal_list_rtl_val.broker_desc = "RETAIL $ VALUE"
            tot_offer = tot_offer + order.offer_amount
            if (order.retail_amt != 0):
                if (abs(float(((order.offer_amount) / float(order.retail_amt)) - 1)) < 0.4):
                    margin40tot = float(margin40tot) + order.retail_amt

        apprisal_list_rtl_val.bonus_eligible = apprisal_list_rtl_val.total_retail_broker - margin40tot

        apprisal_list_tot_val.total_retail_broker_tot = str(round(float(
            apprisal_list_rtl_val.total_retail_broker / apprisal_list_rtl_val.total_retail_broker) * 100,
                                                                  2))
        apprisal_list_tot_val.bonus_eligible_tot = str(
            round((apprisal_list_rtl_val.bonus_eligible / apprisal_list_rtl_val.total_retail_broker) * 100,
                  2))
        apprisal_list_tot_val.hospital_total_tot = apprisal_list_rtl_val.hospital_total + 1
        apprisal_list_tot_val.broker_total_tot = apprisal_list_rtl_val.broker_total + 1
        apprisal_list_tot_val.broker_greater_40_total_tot = apprisal_list_rtl_val.broker_greater_40_total + 1
        apprisal_list_tot_val.broker_less_40_total_tot = apprisal_list_rtl_val.broker_less_40_total + 1
        apprisal_list_rtl_val.broker_desc_tot = "% OF TOTAL"

        apprisal_list_mar_val.total_retail_broker_mar = str(
            round(abs(1 - float(float(tot_offer) / apprisal_list_rtl_val.total_retail_broker)) * 100,
                  2)) + ' %'
        apprisal_list_mar_val.bonus_eligible_mar = str(round(abs(1 - float(
            float(apprisal_list_tot_val.bonus_eligible_tot) / float(
                apprisal_list_tot_val.bonus_eligible_tot))) * 100, 2)) + ' %'
        apprisal_list_mar_val.hospital_total_mar = apprisal_list_rtl_val.hospital_total + 2
        apprisal_list_mar_val.broker_total_mar = apprisal_list_rtl_val.broker_total + 2
        apprisal_list_mar_val.broker_greater_40_total_mar = apprisal_list_rtl_val.broker_greater_40_total + 2
        apprisal_list_mar_val.broker_less_40_total_mar = apprisal_list_rtl_val.broker_less_40_total + 2
        apprisal_list_rtl_val.broker_desc_mar = "MARGIN %"

        apprisal_list_report.append(apprisal_list_rtl_val)
        apprisal_list_report.append(apprisal_list_tot_val)
        apprisal_list_report.append(apprisal_list_mar_val)





