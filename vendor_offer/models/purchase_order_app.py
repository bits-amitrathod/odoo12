from odoo import models, fields, api, _

from datetime import datetime, timedelta
from odoo import models, fields
# from odoo.tools.profiler import profile

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

    t1_retail_amt = fields.Monetary(string='T1 Total Retail Amount', compute="summary_calculate", readonly=True)
    t1_offer_amt = fields.Monetary(string='T1 Total Offer Amount', readonly=True)

    t2_retail_amt = fields.Monetary(string='T2 Total Retail Amount', readonly=True)
    t2_offer_amt = fields.Monetary(string='T2 Total Offer Amount', readonly=True)

    t3_retail_amt = fields.Monetary(string='T3 Total Retail Amount', readonly=True)
    t3_offer_amt = fields.Monetary(string='T3 Total Offer Amount', readonly=True)

    premium_retail_amt = fields.Monetary(string='Premium Total Retail Amount', readonly=True)
    premium_offer_amt = fields.Monetary(string='Premium Total Offer Amount', readonly=True)


    # Convert canceled PO to Vendor Offer Action
    def button_vendor_offer(self):
        _logger.info("Set to VO button Action..")
        self.write({'state': 'ven_draft', 'status': 'ven_draft', 'status_ven': ''})
        if self.import_type_ven != 'all_field_import':
            self.action_po_to_vo_recalculate_vendor_offer()

        return {}

    # Vendor Offer Calculate button Action
    # Calculate Values And Assign
    # @profile
    def action_recalculate_vendor_offer(self):
        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    if obj_line.import_type_ven_line != 'new_appraisal':
                        obj_line.set_values()
                    obj_line.compute_new_fields_vendor_line()
                    if obj.is_change_tier1_to_premium:
                        obj_line.upgrade_multiplier_tier1_to_premium()
                    if obj_line.is_recalculate_multiplier():
                        obj_line.multiplier_adjustment_criteria() if obj.is_dynamic_tier_adjustment else obj_line.no_tier_multiplier_adjustment_criteria()
                    obj_line.copy_product_qty_column()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()
                    obj_line.compute_total_line_vendor()
                    obj_line.compute_average_retail()
                    # obj.summary_calculate(obj_line)

    # This Method used On button_vendor_offer ( PO Convert in to VO )
    def action_po_to_vo_recalculate_vendor_offer(self):
        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    obj_line.set_values()
                    obj_line.compute_new_fields_vendor_line()
                    if obj.is_change_tier1_to_premium:
                        obj_line.upgrade_multiplier_tier1_to_premium()
                    if obj_line.is_recalculate_multiplier():
                        obj_line.multiplier_adjustment_criteria() if obj.is_dynamic_tier_adjustment else obj_line.no_tier_multiplier_adjustment_criteria()
                    obj_line.copy_product_qty_column()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()
                    obj_line.compute_total_line_vendor()
                    obj_line.compute_average_retail()
                    obj.summary_calculate()

    def summary_calculate(self):
        for po in self:
            for line in po.order_line:
                if line.multiplier.name:
                    if 'T 1' in line.multiplier.name:
                        po.t1_retail_amt += line.product_retail
                        po.t1_offer_amt += line.price_subtotal
                    elif 'T 2' in line.multiplier.name:
                        po.t2_retail_amt += line.product_retail
                        po.t2_offer_amt += line.price_subtotal
                    elif line.multiplier.name == "TIER 3":
                        po.t3_retail_amt += line.product_retail
                        po.t3_offer_amt += line.price_subtotal
                    elif line.multiplier.name == "PREMIUM - 50 PRCT":
                        po.premium_retail_amt += line.product_retail
                        po.premium_offer_amt += line.price_subtotal
            po.t1_retail_amt = po.t1_retail_amt

    def check_equipment_present_or_not(self):
        for offer in self:
            offer.offer_contain_equipment = False
            for line in offer.order_line:
                if line.list_contains_equip:
                    offer.offer_contain_equipment = True


