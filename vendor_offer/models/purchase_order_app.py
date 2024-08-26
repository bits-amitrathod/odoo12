from odoo import models, fields, api, _

from datetime import datetime, timedelta
from odoo import models, fields
# from odoo.tools.profiler import Profiler

import logging

_logger = logging.getLogger(__name__)


class VendorOfferNewAppraisal(models.Model):
    _description = "Vendor Offer"
    _inherit = "purchase.order"

    # New fields for removing on change functionality

    no_match_sku_import = fields.Text(string='SKU Cleaned', readonly=True)
    no_match_sku_import_cleaned = fields.Text(string='SKU', readonly=True)

    is_change_tier1_to_premium = fields.Boolean(string="Change Items Priced as Tier 1 to Premium")
    is_dynamic_tier_adjustment = fields.Boolean(string="Allow Dynamic Tier Adjustment?", default=True)
    offer_contain_equipment = fields.Boolean(string="Contains Equipment", compute="check_equipment_present_or_not",)

    t1_retail_amt = fields.Monetary(string='T1 Total Retail Amount', readonly=True)
    t1_offer_amt = fields.Monetary(string='T1 Total Offer Amount', readonly=True)

    t2_retail_amt = fields.Monetary(string='T2 Total Retail Amount', readonly=True)
    t2_offer_amt = fields.Monetary(string='T2 Total Offer Amount', readonly=True)

    t3_retail_amt = fields.Monetary(string='T3 Total Retail Amount', readonly=True)
    t3_offer_amt = fields.Monetary(string='T3 Total Offer Amount', readonly=True)

    premium_retail_amt = fields.Monetary(string='Premium Total Retail Amount', readonly=True)
    premium_offer_amt = fields.Monetary(string='Premium Total Offer Amount', readonly=True)

    is_offers_calculated = fields.Boolean(String='is offer calculated', default=True, store=True)


    def _amount_all(self):
        """
            This method is called everytime a purchase order is open in form for list view for calculations of total prices.
            So we are using this method for our custom calculation as well like of Multipiers and Offer prices at the time
            of import.
            whenever user import the order lines form "New Appraisal" Import button then that import set the Boolean Flag
            to "False" So when  import completed then PO will open in form and then this method will trigger automatically
            and then we do our calculation one time and set the Boolean flag to True so that it will not calculate again
            and again.

            this will resolve our requirement for the calculations at the time of import
        :return:
        """
        if  len(self) == 1 and not self.is_offers_calculated:
            self.action_recalculate_vendor_offer()
            self.is_offers_calculated = True

        res = super(VendorOfferNewAppraisal, self)._amount_all()
        return res

    # Convert canceled PO to Vendor Offer Action
    def button_vendor_offer(self):
        _logger.info("Set to VO button Action..")
        self.write({'state': 'ven_draft', 'status': 'ven_draft', 'status_ven': ''})
        if self.import_type_ven != 'all_field_import':
            self.action_po_to_vo_recalculate_vendor_offer()

        return {}

    # Vendor Offer Calculate button Action
    # Calculate Values And Assign
    def action_recalculate_vendor_offer(self):
        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    obj_line.set_line_initial_values()
                    if obj_line.dont_recalculate_offer_price is not True:
                        obj_line.set_multiplier_as_per_rule_and_data()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()
                    obj_line.set_line_other_values()
                obj.summary_calculate()

    def action_manual_recalculate_vendor_offer(self):
        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    obj_line.set_line_initial_values()

    # This Method used On button_vendor_offer ( PO Convert in to VO )
    def action_po_to_vo_recalculate_vendor_offer(self):
        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    obj_line.set_line_initial_values()
                    if obj_line.is_recalculate_multiplier():
                        obj_line.set_multiplier_as_per_rule_and_data()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()
                    obj_line.set_line_other_values()
                obj.summary_calculate()

    # @profile
    def summary_calculate(self):
        t1_retail_amt,t1_offer_amt = 0, 0
        t2_retail_amt, t2_offer_amt = 0, 0
        t3_retail_amt, t3_offer_amt = 0, 0
        premium_retail_amt, premium_offer_amt = 0, 0
        for po in self:
            for line in po.order_line:
                if line.multiplier.name:
                    if 'T 1' in line.multiplier.name:
                        t1_retail_amt += line.product_retail
                        t1_offer_amt += line.price_subtotal
                    elif 'T 2' in line.multiplier.name:
                        t2_retail_amt += line.product_retail
                        t2_offer_amt += line.price_subtotal
                    elif line.multiplier.name == "TIER 3":
                        t3_retail_amt += line.product_retail
                        t3_offer_amt += line.price_subtotal
                    elif line.multiplier.name == "PREMIUM - 50 PRCT":
                        premium_retail_amt += line.product_retail
                        premium_offer_amt += line.price_subtotal

            po.t1_retail_amt, po.t1_offer_amt = t1_retail_amt, t1_offer_amt
            po.t2_retail_amt, po.t2_offer_amt = t2_retail_amt, t2_offer_amt
            po.t3_retail_amt, po.t3_offer_amt = t3_retail_amt, t3_offer_amt
            po.premium_retail_amt, po.premium_offer_amt = premium_retail_amt, premium_offer_amt

    def check_equipment_present_or_not(self):
        for offer in self:
            offer.offer_contain_equipment = False
            for line in offer.order_line:
                if line.list_contains_equip:
                    offer.offer_contain_equipment = True
