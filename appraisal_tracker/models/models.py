# -*- coding: utf-8 -*-

from odoo import models, fields, api


class apprisal_tracker_vendor(models.Model):

    _inherit = "purchase.order"

    tier1_retail = fields.Char(compute="_value_tier1_retail", store=False)
    tier2_retail = fields.Char(compute="_value_tier2_retail", store=False)
    broker_margin = fields.Char(compute="_value_broker_margin", store=False)

    color = fields.Integer(compute="_value_broker_margin", store=False)

    @api.onchange('broker_margin')
    def _value_broker_margin(self):
        for order in self:

            if(order.rt_price_total_amt!=0):
                if (abs(float(((order.amount_total) / float(order.rt_price_total_amt)) - 1)) < 0.4):
                    order.update({
                        'broker_margin': 'Margin < 40%',
                        'color': 1
                    })
                elif order.partner_id.is_broker:
                    if (abs(float(order.amount_total / order.rt_price_total_amt)) < 0.52):
                        order.update({
                            'broker_margin': 'T1 BROKER',
                            'color': 2
                        })
                    elif (abs(float(order.amount_total / order.rt_price_total_amt)) > 0.52):
                        order.update({
                            'broker_margin': 'T2 BROKER',
                            'color': 3
                        })




