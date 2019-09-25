# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class apprisal_tracker_vendor(models.Model):

    _inherit = "purchase.order"

    tier1_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 1 Retail")
    tier2_retail = fields.Monetary(compute="_value_broker_margin", store=False, string="Tier 2 Retail")
    broker_margin = fields.Char(compute="_value_broker_margin", store=False)

    tier1_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 1 Margin")
    tier2_margin = fields.Char(compute="_value_broker_margin", store=False, string="Tier 2 Margin")
    less_than_40_margin = fields.Char(compute="_value_broker_margin", store=False, string="< 40% Margin")

    color = fields.Integer(compute="_value_broker_margin", store=False)

    t1color = fields.Integer(compute="_value_broker_margin", store=False)
    t2color = fields.Integer(compute="_value_broker_margin", store=False)
    lscolor = fields.Integer(compute="_value_broker_margin", store=False)


    @api.onchange('broker_margin')
    def _value_broker_margin(self):
        for order in self:

            tier1_retail_temp = 0
            tier2_retail_temp = 0
            for line in order.order_line:
                if line.product_id.tier.code == '1':
                    tier1_retail_temp = tier1_retail_temp + line.product_unit_price
                if line.product_id.tier.code == '2':
                    tier2_retail_temp = tier2_retail_temp + line.product_unit_price

            order.update({
                'tier1_retail': tier1_retail_temp,
                'tier2_retail': tier2_retail_temp
            })

            if order.partner_id.is_wholesaler == True:
                if line.product_id.tier.code == '1':
                    if (order.rt_price_total_amt != 0):

                        amt = tier1_retail_temp

                        if(abs(float(amt - 1)) < 0.4):
                            order.update({
                                'less_than_40_margin': 'Margin < 40%',
                                'lscolor': 1
                            })

                        elif ((abs(float(amt - 1)) >= 0.4) and (abs(float(amt - 1)) < 0.48)):
                            order.update({
                                'tier2_margin': 'T2 Wholesaler',
                                't2color': 2
                            })

                        elif ((abs(float(amt - 1)) >= 0.48) ):
                            order.update({
                                'tier1_margin': 'T1 Wholesaler',
                                't1color': 3
                            })
                if line.product_id.tier.code == '2':
                    if (order.rt_price_total_amt != 0):

                        amt = tier2_retail_temp

                        if(abs(float(amt - 1)) < 0.4):
                            order.update({
                                'less_than_40_margin': 'Margin < 40%',
                                'lscolor': 1
                            })

                        elif ((abs(float(amt - 1)) >= 0.4)):
                            order.update({
                                'tier2_margin': 'T2 Wholesaler',
                                't2color': 2
                            })


            else:
                if(order.rt_price_total_amt!=0):
                    if (abs(float(((order.amount_total) / float(order.rt_price_total_amt)) - 1)) < 0.4):
                        order.update({
                            'less_than_40_margin': 'Margin < 40%',
                            'lscolor': 1
                        })
                    elif order.partner_id.is_broker:
                        if (abs(float(order.amount_total / order.rt_price_total_amt)) < 0.52):
                            order.update({
                                'tier1_margin': 'T1 BROKER',
                                't1color': 2
                            })
                        elif (abs(float(order.amount_total / order.rt_price_total_amt)) > 0.52):
                            order.update({
                                'tier2_margin': 'T2 BROKER',
                                't2color': 3
                            })




class CustomerAsWholesaler(models.Model):
    _inherit = 'res.partner'

    is_wholesaler = fields.Boolean(string="Is a Wholesaler?")

    @api.onchange('is_wholesaler', 'is_broker')
    def _check_wholesaler_setting(self):
        warning = {}
        val = {}
        if self.is_broker == True and self.is_wholesaler == True:
            val.update({'is_broker': False})
            warning = {
                'title': _('Warning'),
                'message': _('Customer can be either Wholesaler or Broker , not both'),
            }
        return {'value': val, 'warning': warning}






