from odoo import models, fields, api, _


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

    # def action_recalculate_vendor_offer(self):
    #
    #     for objList in self:
    #         for obj in objList:
    #             for obj_line in obj.order_line:
    #                 obj_line._cal_offer_price()
    #                 obj_line._cal_margin()
    #                 obj_line._set_offer_price()
    #                 obj_line.compute_total_line_vendor()
    #
    #     print('-----------')




