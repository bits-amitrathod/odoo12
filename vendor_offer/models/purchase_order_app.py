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

    # This Method Convert cancelled PO -> Vendor Offer
    def button_vendor_offer(self):
        _logger.info("Set to VO button Action..")
        self.write({'state': 'ven_draft', 'status': 'ven_draft', 'status_ven': ''})
        self.action_recalculate_vendor_offer()
        return {}

    def action_recalculate_vendor_offer(self):

        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    obj_line.set_values()
                    if obj.is_change_tier1_to_premium:
                        pass  # TODO : Tier 1 products multiplier increased to Premium
                    if obj_line.is_recalculate_multiplier():
                        obj_line.multiplier_adjustment_criteria() if obj.is_dynamic_tier_adjustment else obj_line.no_tier_multiplier_adjustment_criteria()
                    obj_line.copy_product_qty_column()
                    obj_line._cal_offer_price()
                    obj_line._set_offer_price()
                    obj_line._cal_margin()

                    obj_line.compute_total_line_vendor()
                    # obj_line.compute_retail_line_total()

        print('-----------')
