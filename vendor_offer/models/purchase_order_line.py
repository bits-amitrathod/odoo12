import datetime
import logging
from random import randint

import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from werkzeug.urls import url_encode


class VendorOfferProduct(models.Model):
    _inherit = "purchase.order.line"
    _description = "Vendor Offer Product"

    product_tier = fields.Many2one('tier.tier', string="Tier", compute='onchange_product_id_vendor_offer')
    sku_code = fields.Char('Product SKU', compute='onchange_product_id_vendor_offer', store=False)
    product_brand_id = fields.Many2one('product.brand', string='Manufacture',
                                       compute='onchange_product_id_vendor_offer',
                                       help='Select a Manufacture for this product', store=False)
    product_sales_count = fields.Integer(string="Sales All", readonly=True, store=True)
    product_sales_count_month = fields.Integer(string="Sales Month", readonly=True, store=True)
    product_sales_count_90 = fields.Integer(string="Sales 90", readonly=True, store=True)
    product_sales_count_yrs = fields.Integer(string="Sales Yr", readonly=True, store=True)
    qty_in_stock = fields.Integer(string="Quantity In Stock", readonly=True, compute='onchange_product_id_vendor_offer',
                                  store=True)
    expiration_date = fields.Datetime(string="Expiration Date", readonly=True, )
    expiration_date_str = fields.Char(string="Expiration Date")
    uom_str = fields.Char(string="UOM")
    expired_inventory = fields.Char(string="Expired Inv", compute='onchange_product_id_vendor_offer',
                                    readonly=True,
                                    store=True)
    multiplier = fields.Many2one('multiplier.multiplier', string="Multiplier")

    possible_competition = fields.Many2one(related='order_id.possible_competition', store=False)
    # accelerator = fields.Boolean(related='order_id.accelerator')
    # max = fields.Char(related='order_id.max')
    # rt_price_total_amt = fields.Monetary(related='order_id.rt_price_total_amt')
    vendor_offer_data = fields.Boolean(related='order_id.vendor_offer_data')
    product_note = fields.Text(string="Notes")

    margin = fields.Char(string="Cost %", readonly=True, compute='_cal_margin')
    # product_unit_price = fields.Monetary(string="Retail Price",default='_cal_offer_price' , store=True)
    # product_offer_price = fields.Monetary(string="Offer Price", readonly=True, compute='cal_offer_price')
    for_print_product_offer_price = fields.Char(string="Offer Price")
    for_print_price_subtotal = fields.Char(string="Offer Price")
    product_retail = fields.Monetary(string="Total Retail Price", compute='_compute_amount')
    rt_price_total = fields.Monetary(compute='_compute_amount', string='Total')
    rt_price_tax = fields.Monetary(compute='_compute_amount', string='Tax')
    import_type_ven_line = fields.Char(string='Import Type of Product for calculation')

    delivered_product_offer_price = fields.Monetary("Total Received Qty Offer Price", store=False,
                                                    compute="_calculat_delv_price")
    delivered_product_retail_price = fields.Monetary("Total Received Qty Retail Price", store=False,
                                                     compute="_calculat_delv_price")

    billed_product_offer_price = fields.Monetary("Total Billed Qty Offer Price", store=False,
                                                    compute="_calculat_bill_price")
    billed_product_retail_price = fields.Monetary("Total Billed Qty Retail Price", store=False,
                                                     compute="_calculat_bill_price")



    #@api.multi
    def _calculat_delv_price(self):
        for order in self:
            for p in order:
                order.delivered_product_offer_price = round(p.qty_received * p.product_offer_price, 2)
                order.delivered_product_retail_price = round(p.qty_received * p.product_unit_price, 2)

    #@api.multi
    def _calculat_bill_price(self):
        for order in self:
            for p in order:
                order.billed_product_offer_price = round(p.qty_invoiced * p.product_offer_price, 2)
                order.billed_product_retail_price = round(p.qty_invoiced * p.product_unit_price, 2)


    def action_show_details(self):
        multi = self.env['stock.move'].search([('purchase_line_id', '=', self.id)])
        if len(multi) >= 1 and self.order_id.picking_count == 1:
            return multi.action_show_details()
        elif self.order_id.picking_count > 1:
            raise ValidationError(_('Picking is not possible for multiple shipping please do picking inside Shipping'))

    def set_values_from_import(self):
        pass

    @api.onchange('product_id')
    @api.depends('product_id')
    def onchange_product_id_vendor_offer(self):
        for line in self:
            line.product_tier = line.product_id.product_tmpl_id.tier

            line.sku_code = line.product_id.product_tmpl_id.sku_code
            line.product_brand_id = line.product_id.product_tmpl_id.product_brand_id
            # total = total_m = total_90 = total_yr = 0
            # str_query_cm = "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON " \
            #                "sp.sale_id=sol.id " \
            #                " LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND " \
            #                "sml.location_dest_id =%s AND" \
            #                " sml.product_id =%s"
            # cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            # today_date = datetime.datetime.now()
            # last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))

            if line.env.context.get('vendor_offer_data') or line.state == 'ven_draft' or line.state == 'ven_sent':
                result1 = {}
                if not line.product_id:
                    return result1
                if line.product_qty_app_new is False or line.product_qty_app_new == 0.0:
                    line.product_qty_app_new = 1
                if line.order_id.import_type_ven != 'new_appraisal':

                    ''' sale count will show only done qty '''

                    # last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
                    # last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
                    #
                    # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                    #                                                              line.product_id.id, last_month))
                    # quant_m = self.env.cr.fetchone()
                    # if quant_m[0] is not None:
                    #     total_m = total_m + int(quant_m[0])
                    # line.product_sales_count_month = total_m
                    #
                    # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                    #                                                              line.product_id.id, last_3_months))
                    # quant_90 = self.env.cr.fetchone()
                    # if quant_90[0] is not None:
                    #     total_90 = total_90 + int(quant_90[0])
                    # line.product_sales_count_90 = total_90
                    #
                    # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                    #                                                              line.product_id.id, last_yr))
                    # quant_yr = self.env.cr.fetchone()
                    # if quant_yr[0] is not None:
                    #     total_yr = total_yr + int(quant_yr[0])
                    # line.product_sales_count_yrs = total_yr
                    #
                    # self.env.cr.execute(str_query_cm, (cust_location_id, line.product_id.id))
                    # quant_all = self.env.cr.fetchone()
                    # if quant_all[0] is not None:
                    #     total = total + int(quant_all[0])
                    # line.product_sales_count = total

                    line.qty_in_stock = line.product_id.qty_available

                    if line.order_id.is_dynamic_tier_adjustment:
                        line.multiplier_adjustment_criteria()
                    else:
                        line.no_tier_multiplier_adjustment_criteria()

                    # if line.multiplier.id == False:
                    #     if line.product_tier.code == False:
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'out of scope')])
                    #         line.multiplier = multiplier_list.id
                    #     elif line.product_sales_count == 0:
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'no history')])
                    #         line.multiplier = multiplier_list.id
                    #     elif float(line.qty_in_stock) > (
                    #             line.product_sales_count * 2) and line.product_sales_count != 0:
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'overstocked')])
                    #         line.multiplier = multiplier_list.id
                    #     elif line.product_id.product_tmpl_id.premium == True:
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'premium')])
                    #         line.multiplier = multiplier_list.id
                    #     elif line.product_tier.code == '1':
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 't1 good 45')])
                    #         line.multiplier = multiplier_list.id
                    #     elif line.product_tier.code == '2':
                    #         multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 't2 good 35')])
                    #         line.multiplier = multiplier_list.id

                    # line.update_product_expiration_date()

                    if (line.product_qty == False):
                        line.product_qty = '1'
                        # line.price_subtotal = line.list_price ???
                        # line.product_unit_price = line.list_price

                    self.expired_inventory_cal(line)

    def expired_inventory_cal(self, line):
        expired_lot_count = 0
        test_id_list = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id)])
        for prod_lot in test_id_list:
            if prod_lot.use_date:
                if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                    expired_lot_count = expired_lot_count + 1

        line.expired_inventory = expired_lot_count

    # @api.onchange('multiplier', 'order_id.possible_competition')
    # @api.depends('multiplier', 'order_id.possible_competition')
    def _cal_offer_price(self):
        for line in self:
            # if line.import_type_ven_line == all_field_import:
            #     if 'order_list_list' in request.session:
            #         VendorOfferProduct.set_values_from_import(line)
            # else:
            multiplier_list = line.multiplier
            # Added to fix inhirit issue

            # product_unit_price = math.floor(
            #     round(float(line.product_id.list_price) * (float(multiplier_list.retail) / 100), 2))

            val_t = float(line.product_id.list_price) * (float(multiplier_list.retail) / 100)
            if (float(val_t) % 1) >= 0.5:
                product_unit_price = math.ceil(
                    float(line.product_id.list_price) * (float(multiplier_list.retail) / 100))

            else:
                product_unit_price = math.floor(
                    float(line.product_id.list_price) * (float(multiplier_list.retail) / 100))

            margin = 0
            if line.multiplier.id:
                margin += line.multiplier.margin

            if line.possible_competition.id:
                margin += line.possible_competition.margin

            line.update({
                'margin': margin
            })

            if line.dont_recalculate_offer_price is not True:
                line.update({
                    'product_unit_price': product_unit_price,
                })

    product_unit_price = fields.Monetary(string="Retail Price", default=_cal_offer_price, store=True)

    # @api.onchange('multiplier', 'order_id.possible_competition')
    # @api.depends('multiplier', 'order_id.possible_competition')
    def _cal_margin(self):
        for line in self:
            margin = 0
            if line.multiplier.id:
                margin += line.multiplier.margin

            if line.possible_competition.id:
                margin += line.possible_competition.margin

            line.update({
                'margin': margin
            })

    # @api.onchange('multiplier', 'order_id.possible_competition')
    # @api.depends('multiplier', 'order_id.possible_competition')
    def _set_offer_price(self):
        for line in self:
            # if line.import_type_ven_line == all_field_import:
            #     if 'order_list_list' in request.session:
            #         VendorOfferProduct.set_values_from_import(line)
            # else:
            multiplier_list = line.multiplier

            # product_unit_price = math.floor(
            #     round(float(line.product_id.list_price) * (float(multiplier_list.retail) / 100), 2))
            # product_offer_price = math.floor(float(product_unit_price) * (
            #         float(multiplier_list.margin) / 100 + float(line.possible_competition.margin) / 100))

            val_t = float(line.product_id.list_price) * (float(multiplier_list.retail) / 100)
            if (float(val_t) % 1) >= 0.5:
                product_unit_price = math.ceil(
                    float(line.product_id.list_price) * (float(multiplier_list.retail) / 100))

            else:
                product_unit_price = math.floor(
                    float(line.product_id.list_price) * (float(multiplier_list.retail) / 100))

            val_off = float(product_unit_price) * (float(
                multiplier_list.margin) / 100 + float(line.possible_competition.margin) / 100)
            if (float(val_off) % 1) >= 0.5:
                product_offer_price = math.ceil(
                    float(product_unit_price) * (
                            float(multiplier_list.margin) / 100 + float(
                        line.possible_competition.margin) / 100))

            else:
                product_offer_price = math.floor(float(product_unit_price) * (
                        float(multiplier_list.margin) / 100 + float(
                    line.possible_competition.margin) / 100))

            if line.dont_recalculate_offer_price is not True:
                line.update({
                    'product_offer_price': product_offer_price
                })

    product_offer_price = fields.Monetary(string="Offer Price", default=_set_offer_price, store=True)

    # def update_product_expiration_date(self):
    #     for order in self:
    #         order.env.cr.execute(
    #             "SELECT min(use_date), max(use_date) FROM public.stock_production_lot where product_id =" + str(
    #                 order.product_id.id))
    #         query_result = order.env.cr.dictfetchone()
    #         if query_result['max'] != None:
    #             self.expiration_date = fields.Datetime.from_string(str(query_result['max'])).date()

    @api.onchange('product_qty', 'product_offer_price', 'taxes_id')
    @api.depends('product_qty', 'product_offer_price', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            if line.env.context.get('vendor_offer_data') or line.state == 'ven_draft' or line.state == 'ven_sent':

                taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                                   line.product_qty, product=line.product_id,
                                                   partner=line.order_id.partner_id)

                taxes = line.taxes_id.compute_all(float(line.product_offer_price), line.order_id.currency_id,
                                                  line.product_qty, product=line.product_id,
                                                  partner=line.order_id.partner_id)
                #if line.order_id.import_type_ven != 'new_appraisal':
                if line.order_id.import_type_ven != 'all_field_import':
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_subtotal': taxes['total_excluded'],
                        'price_total': taxes['total_included'],
                        'price_unit': line.product_offer_price,

                        'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                        'product_retail': taxes1['total_excluded'],
                        'rt_price_total': taxes1['total_included'],
                    })
                else:
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_subtotal': taxes['total_excluded'],
                        'price_total': taxes['total_included'],
                        'price_unit': line.product_offer_price,

                        'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                        'product_retail': taxes1['total_excluded'],
                        'rt_price_total': taxes1['total_included'],
                    })

                # else:
                #     line.update({
                #         'price_tax': line.price_tax,
                #         'price_subtotal': line.price_subtotal,
                #         'price_total': line.price_total,
                #         'price_unit': line.price_unit,
                #
                #         'rt_price_tax': line.rt_price_tax,
                #         'product_retail': line.product_retail,
                #         'rt_price_total': line.rt_price_total,
                #     })

            else:
                taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                                   line.product_qty, product=line.product_id,
                                                   partner=line.order_id.partner_id)
                line.update({
                    'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                    'product_retail': taxes1['total_excluded'],
                    'rt_price_total': taxes1['total_included'],
                })

                # super(VendorOfferProduct, self)._compute_amount()
