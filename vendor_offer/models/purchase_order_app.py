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

    # This Method Convert cancelled PO -> Vendor Offer
    def button_vendor_offer(self):
        _logger.info("Set to VO button Action..")
        self.write({'state': 'ven_draft'})
        self.action_recalculate_vendor_offer()
        return {}

    def get_quotations_count_by_product(self, product):
        orders = self.env['sale.order'].search([('state', 'in', ['draft', 'sent'])])
        quotations = orders.filtered(lambda order: product.id in order.order_line.mapped('product_id.id'))
        return len(quotations) if quotations else 0

    def get_last_year_sales_by_product(self):
        return 1000

    def multiplier_adjustment_criteria(self, po_line):
        if po_line:
            qty_in_stock = po_line.qty_in_stock
            product_sales_count = po_line.product_sales_count   # qty_sold_all
            qty_sold_yr = po_line.product_sales_count_yrs
            tier = po_line.product_id.tier
            open_quotations_cnt = self.get_quotations_count_by_product(po_line.product_id)
            qty_sold_90_days = po_line.product_sales_count_90
            average_aging = po_line.product_id.average_aging
            inv_ratio_90_days = 0                    #TODO: Calulare after
            product_sales_total_amount_yr = self.get_last_year_sales_by_product()    #TODO: make change

            if qty_in_stock == 0 and product_sales_count == 0:
                if 0 < open_quotations_cnt < 5:
                    multiplier = 'TIER 3'
                elif 5 <= open_quotations_cnt <= 15:
                    multiplier = 'T2 Good – 35 PRCT'
                elif open_quotations_cnt > 15:
                    multiplier = 'T1 Good – 45 PRCT'
            elif tier == 1 and inv_ratio_90_days < 1:
                if product_sales_total_amount_yr >= 100000 or open_quotations_cnt >= 20 or qty_in_stock == 0:
                    multiplier = 'Premium – 50 PRCT'
            elif tier == 2 and inv_ratio_90_days < 1:
                if open_quotations_cnt >= 10 or (qty_in_stock == 0 and qty_sold_90_days > 0):
                    multiplier = 'T1 Good – 45 PRCT'
            elif qty_sold_yr >= qty_in_stock > 0 and qty_sold_90_days == 0 and product_sales_count == 0 and average_aging > 30:
                multiplier = 'TIER 3'
            elif qty_in_stock == 0 and qty_sold_yr == 0 and product_sales_count == 0 and open_quotations_cnt < 5:
                multiplier = 'TIER 3'

            # Change TIER 3 To multiplier this is for only testing purpose
            multiplier = 'TIER 3'
            po_line.multiplier = self.env['multiplier.multiplier'].search([('name', '=', multiplier)], limit=1)

    def action_recalculate_vendor_offer(self):

        for objList in self:
            for obj in objList:
                for obj_line in obj.order_line:
                    # obj_line._cal_offer_price()
                    obj.multiplier_adjustment_criteria(obj_line)
                    obj_line._cal_margin()
                    obj_line._set_offer_price()
                    obj_line.compute_total_line_vendor()
                    # obj_line.compute_retail_line_total()


        print('-----------')
