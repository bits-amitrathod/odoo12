from odoo import models, fields, api, _

from datetime import datetime, timedelta
from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class VendorOfferNewAppraisal(models.Model):
    _description = "Vendor Offer"
    _inherit = "purchase.order"

    # New fields for removing on change functionality

    # credit_amount_untaxed_app_new = fields.Monetary(string='Untaxed Credit Offer Price', readonly=True)
    # credit_amount_total_app_new = fields.Monetary(string='Total Credit Offer Price', readonly=True)
    # cash_amount_untaxed_app_new = fields.Monetary(string='Untaxed Credit Offer Price', readonly=True)
    # cash_amount_total_app_new = fields.Monetary(string='Total Credit Offer Price', readonly=True)
    #
    # billed_retail_untaxed_app_new = fields.Monetary(string='Billed Untaxed Retail', readonly=True)
    # billed_retail_total_app_new = fields.Monetary(string='Billed Retail Total', readonly=True)
    #
    # billed_offer_untaxed_app_new = fields.Monetary(string='Billed Untaxed Offer', readonly=True)
    # billed_offer_total_app_new = fields.Monetary(string='Billed Offer Total', readonly=True)

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


    # This Method Convert cancelled PO -> Vendor Offer
    def button_vendor_offer(self):
        _logger.info("Set to VO button Action..")
        self.write({'state': 'ven_draft', 'status': 'ven_draft', 'status_ven': ''})
        self.action_recalculate_vendor_offer()
        return {}

    def action_recalculate_vendor_offer(self):

        for objList in self:
            for obj in objList:
                obj.set_zero_val()
                for obj_line in obj.order_line:
                    obj_line.set_values()
                    if obj.is_change_tier1_to_premium:
                        obj_line.upgrade_multiplier_tier1_to_premium()
                    if obj_line.is_recalculate_multiplier():
                        obj_line.multiplier_adjustment_criteria() if obj.is_dynamic_tier_adjustment else obj_line.no_tier_multiplier_adjustment_criteria()
                    obj_line.copy_product_qty_column()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()

                    obj_line.compute_total_line_vendor()
                    obj_line.compute_new_fields_vendor_line()
                    obj_line.compute_average_retail()
                    # obj_line.compute_retail_line_total()
                    obj.summary_calculate(obj_line)

        print('-----------')

    def set_zero_val(self):
        self.t1_retail_amt = 0
        self.t1_offer_amt = 0
        self.t2_retail_amt = 0
        self.t2_offer_amt = 0
        self.t3_retail_amt = 0
        self.t3_offer_amt = 0
        self.premium_retail_amt = 0
        self.premium_offer_amt = 0

    def summary_calculate(self, line):
        if 'T1' in line.multiplier.name:
            self.t1_retail_amt += line.product_retail
            self.t1_offer_amt += line.price_subtotal
        elif 'T2' in line.multiplier.name:
            self.t2_retail_amt += line.product_retail
            self.t2_offer_amt += line.price_subtotal
        elif line.multiplier.name == "TIER 3":
            self.t3_retail_amt += line.product_retail
            self.t3_offer_amt += line.price_subtotal
        elif line.multiplier.name == "PREMIUM - 50 PRCT":
            self.premium_retail_amt += line.product_retail
            self.premium_offer_amt += line.price_subtotal

    def check_equipment_present_or_not(self):
        for offer in self:
            for line in offer.order_line:
                offer.offer_contain_equipment = False
                if line.list_contains_equip:
                    offer.offer_contain_equipment = True


