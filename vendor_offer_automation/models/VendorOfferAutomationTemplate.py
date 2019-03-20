# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VendorOfferAutomationTemplate(models.Model):
    _description = "Vendor Offer Automation Template"
    _name = "sps.vendor_offer_automation.template"

    # customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    file_name = fields.Char('File Name')
    template_status = fields.Char('Template Status')
    columns_from_template = fields.Char('Columns of Template')

    mf_product_description = fields.Char(string='Product Name')
    mf_customer_sku = fields.Char(string='SKU', required=True)
    mf_quantity_in_stock = fields.Char(string='Quantity In Stock')
    mf_quantity = fields.Char(string='Required Quantity')
    mf_expiration_date = fields.Char(string='Expiration Date')
    mf_uom = fields.Char(string='Unit Of Measurement')