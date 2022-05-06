# -*- coding: utf-8 -*-

from odoo import models, fields, api

hide_column_list_method = ['mf_product_description', 'mf_quantity_in_stock', 'mf_uom','mf_price', 'mf_sales_count',
                           'mf_sales_count_yr', 'mf_sales_total', 'mf_premium', 'mf_exp_inventory', 'mf_sales_count_90',
                           'mf_offer_price', 'mf_offer_price_total', 'mf_retail_price', 'mf_retail_price_total',
                           'mf_possible_competition', 'mf_multiplier', 'mf_potential_profit_margin', 'mf_max',
                           'mf_accelerator','mf_credit','mf_margin_cost']
all_field_import = 'all_field_import'
few_field_import = 'few_field_import'


class VendorOfferAutomationTemplateClass(models.Model):
    _description = "Vendor Offer Automation Template"
    _name = "sps.vendor_offer_automation.template"

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    file_name = fields.Char('File Name')
    template_status = fields.Char('Template Status')
    columns_from_template = fields.Char('Columns of Template')

    #mf_product_description = fields.Char(string='Product Name')
    mf_customer_sku = fields.Char(string='ProductNumber', required=True)
    #mf_quantity_in_stock = fields.Char(string='Qty In Stock')
    mf_quantity = fields.Char(string='Quantity')
    mf_expiration_date = fields.Char(string='Expiration Date')
    #mf_uom = fields.Char(string='Unit Of Measurement')

    mf_price = fields.Char(string='Price')
    # mf_sales_count = fields.Char(string='Sales Count')
    # mf_sales_count_yr = fields.Char(string='Sales Count YR')
    # mf_sales_total = fields.Char(string='Sales Total')
    # mf_premium = fields.Char(string='Premium')
    # mf_exp_inventory = fields.Char(string='Exp Inventory')
    # mf_sales_count_90 = fields.Char(string='Sales Count 90')

    mf_offer_price = fields.Char(string='Offer Price')
    mf_offer_price_total = fields.Char(string='Total Offer Price')
    mf_retail_price = fields.Char(string='Retail Price')
    mf_retail_price_total = fields.Char(string='Total Retail Price')

    mf_possible_competition = fields.Char(string='Possible Competition')
    mf_multiplier = fields.Char(string='Multiplier')
    mf_potential_profit_margin = fields.Char(string='Potential Profit Margin')
    mf_max = fields.Char(string='Max')

    mf_accelerator = fields.Char(string='Accelerator')
    mf_credit = fields.Char(string='Credit')
    #mf_margin_cost = fields.Char(string='Cost %')
