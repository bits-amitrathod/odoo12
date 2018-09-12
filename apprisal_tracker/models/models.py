# -*- coding: utf-8 -*-

from odoo import models, fields, api

class apprisal_tracker(models.Model):
    _name = 'apprisal_tracker.apprisal_tracker'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        self.value2 = float(self.value) / 100




class apprisal_tracker_vendor(models.Model):

    _inherit = "purchase.order"

    tier1_retail = fields.Char(compute="_value_tier1_retail", store=False)
    tier2_retail = fields.Char(compute="_value_tier2_retail", store=False)
    broker_margin = fields.Char(compute="_value_broker_margin", store=False)
    color = fields.Char(compute="_value_color", store=False)

    @api.onchange('tier1_retail')
    def _value_tier1_retail(self):
        for order in self:
            order.tier1_retail="100"


    @api.onchange('tier2_retail')
    def _value_tier2_retail(self):
        for order in self:
            order.tier2_retail="200"

    @api.onchange('color')
    def _value_color(self):
        return 'red'

    @api.onchange('broker_margin')
    def _value_broker_margin(self):
        for order in self:
            if(order.retail_amt!=0):
                if(abs(float(((order.offer_amount)/float(order.retail_amt))-1)) < 0.4):
                    order.broker_margin='Margin < 40%'
                    order.color="red"
                elif(order.partner_id.is_broker):
                    if(abs(float(order.offer_amount/order.retail_amt)) < 0.52):
                        order.broker_margin = 'T1 BROKER'
                        order.color = "blue"
                    elif(abs(float(order.offer_amount/order.retail_amt)) > 0.52):
                        order.broker_margin = 'T2 BROKER'
                        order.color = "yellow"



