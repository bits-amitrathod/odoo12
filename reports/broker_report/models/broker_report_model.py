# -*- coding: utf-8 -*-

from odoo import models, fields, api


class broker_report(models.Model):
    _inherit = 'purchase.order'

    total_retail_broker = fields.Monetary('Total Retail', store=False)
    bonus_eligible = fields.Monetary(string='Bonus Eligible', store=False)
    hospital_total = fields.Monetary(string='Hospital Total',store=False)
    broker_total = fields.Monetary('Broker Total', store=False)
    broker_greater_40_total = fields.Monetary(string='Broker > 40% Total', store=False)
    broker_less_40_total = fields.Monetary('Broker < 40% Total', store=False)
    broker_desc = fields.Char('Desc', store=False)

    total_retail_broker_tot = fields.Char('Total Retail', store=False)
    bonus_eligible_tot = fields.Char(string='Bonus Eligible', store=False)
    hospital_total_tot = fields.Char(string='Hospital Total', store=False)
    broker_total_tot = fields.Char('Broker Total', store=False)
    broker_greater_40_total_tot = fields.Char(string='Broker > 40% Total', store=False)
    broker_less_40_total_tot = fields.Char('Broker < 40% Total', store=False)
    broker_desc_tot = fields.Char('Desc', store=False)

    total_retail_broker_mar = fields.Char('Total Retail', store=False)
    bonus_eligible_mar = fields.Char(string='Bonus Eligible', store=False)
    hospital_total_mar = fields.Char(string='Hospital Total', store=False)
    broker_total_mar = fields.Char('Broker Total', store=False)
    broker_greater_40_total_mar = fields.Char(string='Broker > 40% Total', store=False)
    broker_less_40_total_mar = fields.Char('Broker < 40% Total', store=False)
    broker_desc_mar = fields.Char('Desc', store=False)

    data_state = fields.Char('', store=False)
