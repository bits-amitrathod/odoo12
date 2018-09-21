# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError,ValidationError
import datetime
import math
from random import randint


class VendorOffer(models.Model):

    _description = "Vendor Offer"
    _inherit = "purchase.order"

    vendor_offer_data = fields.Boolean()
    status_ven = fields.Char( store=True, string="Status")
    carrier_info = fields.Char("Carrier Info", related='partner_id.carrier_info', readonly=True)
    carrier_acc_no = fields.Char("Carrier Account No", related='partner_id.carrier_acc_no', readonly=True)
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    appraisal_no = fields.Char(string='Appraisal No#',compute="_default_appraisal_no",readonly=False,store=True)
    acq_user_id = fields.Many2one('res.users',string='Acq  Manager ')
    date_offered = fields.Datetime(string='Date Offered', default=fields.Datetime.now)
    revision = fields.Integer(string='Revision ')
    max = fields.Char(string='Max',  default=0)
    potential_profit_margin = fields.Char(string='Potential Profit Margin', default=0)
    accepted_date = fields.Datetime(string="Accepted Date")
    declined_date = fields.Datetime(string="Declined Date")
    retail_amt = fields.Monetary(string="Total Retail",readonly=True,default=0 ,compute='_amount_tot_all')
    offer_amount = fields.Monetary(string="Total  Offer",readonly=True,default=0,compute='_amount_tot_all')
    # date_planned = fields.Datetime(string='Scheduled Date')
    possible_competition = fields.Many2one('competition.competition', string="Possible Competition")
    offer_type = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit')
    ], string='Offer Type')

    shipping_date = fields.Datetime(string="Shipping Date")
    delivered_date = fields.Datetime(string="Delivered Date")
    expected_date = fields.Datetime(string="Expected Date")

    notes_desc = fields.Text(string="Note")

    accelerator=fields.Boolean(string="Accelerator")
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')], string='Priority')

    new_customer = fields.Boolean(string="New Customer")
    shipping_label_issued = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Shipping label Issued')

    status = fields.Selection([
        ('ven_draft', 'Vendor Offer'),
        ('ven_sent', 'Vendor Offer Sent'),
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='ven_draft',track_visibility='onchange',store=True)

    state = fields.Selection([
        ('ven_draft', 'Vendor Offer'),
        ('ven_sent', 'Vendor Offer Sent'),
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    def action_validate(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) == 1 and self.picking_count ==1:
            return multi.button_validate()
        elif self.picking_count > 1:
            raise ValidationError(_('Validate is not possible for multiple Shipping please do validate one by one'))

    def action_assign(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.action_assign()

    def _compute_show_validate(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi)>=1:
            multi._compute_show_validate()

    @api.multi
    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

    def test_00_purchase_order_flow(self):
        pass

    @api.onchange('appraisal_no')
    def _default_appraisal_no(self):
        for order in self:
            if(order.appraisal_no == False):
                order.appraisal_no = 'AP' + str(randint(11111, 99999))


    @api.depends('order_line.product_offer_price')
    def _amount_tot_all(self):
        for order in self:
            retail_amt = offer_amount = 0.0
            for line in order.order_line:
                retail_amt += float(line.product_retail)
                offer_amount += float(line.price_subtotal)
            # order.retail_amt =retail_amt
            # order.offer_amount = offer_amount
            order.update({
                'retail_amt': retail_amt,
                'offer_amount': offer_amount,
            })

    @api.onchange('possible_competition')
    def possible_competition_onchange(self):
        self.state = 'ven_draft'
        for order in self:
            for line in order.order_line:
                multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                possible_competition_list = self.env['competition.competition'].search([('id', '=', self.possible_competition.id)])
                line.product_unit_price = math.ceil(
                    round(float(line.list_price) * (float(multiplier_list.retail) / 100), 2))
                line.product_offer_price = math.ceil(round(float(line.product_unit_price) * (
                            float(multiplier_list.margin) / 100 + float(possible_competition_list.margin) / 100), 2))

    @api.onchange('offer_amount', 'retail_amt')
    def cal_potentail_profit_margin(self):
        if(self.retail_amt!=0):
            self.potential_profit_margin = math.ceil(abs(round((((self.offer_amount/self.retail_amt)*100)-100),2)))

    @api.onchange('accelerator','retail_amt')
    def accelerator_onchange(self):
        if self.accelerator == True:
            self.max = round(float(self.retail_amt)*float(0.65),2)
        else:
            self.max = 0

    @api.multi
    def action_send_offer_email(self):
        pass

    @api.multi
    def action_print_vendor_offer(self):
        pass

    @api.multi
    def action_confirm_vendor_offer(self):
        self.write({'state': 'purchase'})
        self.write({'status': 'purchase'})
        self.write({'status_ven': 'Accepted'})
        self.write({'accepted_date': fields.date.today()})
        if (self.revision > 0):
            temp = self.revision - 1
            self.revision = temp
        return True

    @api.multi
    def action_cancel_vendor_offer(self):
        self.write({'state': 'cancel'})
        self.write({'status': 'cancel'})
        self.write({'status_ven': 'Declined'})
        self.write({'declined_date': fields.date.today()})



    @api.model
    def create(self, vals):
        if(self.env.context.get('vendor_offer_data') == True):
            vals['state']= 'ven_draft'
            vals['vendor_offer_data']=True
            vals['revision'] = 0
        return super(VendorOffer, self).create(vals)

    @api.multi
    def write(self, values):
        if (self.state == 'ven_draft'):
            temp = self.revision + 1
            values['revision'] = temp
        return super(VendorOffer, self).write(values)



class VendorOfferProduct(models.Model):

    _inherit = "purchase.order.line"
    _inherits = {'product.product': 'product_id'}
    _description = "Vendor Offer Product"

    product_tier = fields.Many2one('tier.tier', string="Tier")
    product_sales_count = fields.Char(string="Sales Count All")
    product_sales_count_month = fields.Char(string="Sales Count Month")
    product_sales_count_90 = fields.Char(string="Sales Count 90 Days")
    product_sales_count_yrs = fields.Char(string="Sales Count Yr")
    qty_in_stock = fields.Char(string="Quantity In Stock")
    expiration_date = fields.Datetime(string="Expiration Date")
    expired_inventory = fields.Char(string="Expired Inventory Items")
    multiplier = fields.Many2one('multiplier.multiplier', string="Multiplier")
    offer_price = fields.Char(string="Total Offer Price")
    product_offer_price = fields.Char(string="Offer Price")
    margin = fields.Char(string="Margin")
    possible_competition = fields.Many2one(related='order_id.possible_competition',store=False)
    vendor_offer_data = fields.Boolean(related='order_id.vendor_offer_data', store=True)
    product_note = fields.Text(string="Notes")
    product_retail = fields.Char(string="Total Retail Price")
    product_unit_price = fields.Char(string="Retail Price")

    def action_show_details(self):

        multi = self.env['stock.move'].search([('purchase_line_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.action_show_details()

    @api.depends('product_qty', 'list_price', 'taxes_id','product_offer_price')
    def _compute_amount(self):
        for line in self:
            super(VendorOfferProduct, self)._compute_amount()
            if(line.state=='ven_draft'):
                multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                line.margin=multiplier_list.margin
                line.product_retail=round(float(line.product_qty) * float(line.product_unit_price),2)
                # line.price_subtotal = round(float(line.product_qty) * float(line.product_unit_price),2)
                line.price_subtotal = round(float(line.product_qty) * float(line.product_offer_price),2)
                line.update({
                    'price_tax': '0',
                    'price_subtotal': line.price_subtotal,
                })

    @api.onchange('product_id')
    def onchange_product_id_vendor_offer(self):
        if (self.state == 'ven_draft'):
            result1 = {}
            if not self.product_id:
                return result1

            self.qty_in_stocks()
            groupby_dict = groupby_dict_month = groupby_dict_90 = groupby_dict_yr = {}
            sale_orders_line = self.env['sale.order.line'].search([('product_id', '=', self.product_id.id),('state','=','sale')])
            groupby_dict['data'] = sale_orders_line
            total = total_m = total_90 = total_yr = 0

            for sale_order in groupby_dict['data']:
                total=total + sale_order.product_uom_qty

            self.product_sales_count=total
            sale_orders = self.env['sale.order'].search([('product_id', '=', self.product_id.id),('state','=','sale')])
            # date_planned = fields.Datetime(string='Scheduled Date', compute='_compute_date_planned', store=True, index=True)

            filtered_by_date = list(
                        filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (fields.date.today() - datetime.timedelta(days=30)), sale_orders))
            groupby_dict_month['data'] = filtered_by_date
            for sale_order_list in groupby_dict_month['data']:
                for sale_order in sale_order_list.order_line:
                    if sale_order.product_id.id == self.product_id.id:
                        total_m=total_m + sale_order.product_uom_qty

            self.product_sales_count_month=total_m

            filtered_by_90 = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (fields.date.today() - datetime.timedelta(days=90)), sale_orders))
            groupby_dict_90['data'] = filtered_by_90

            for sale_order_list_90 in groupby_dict_90['data']:
                for sale_order in sale_order_list_90.order_line:
                    if sale_order.product_id.id == self.product_id.id:
                        total_90 = total_90 + sale_order.product_uom_qty

            self.product_sales_count_90 = total_90

            filtered_by_yr = list(filter(lambda x: fields.Datetime.from_string(x.confirmation_date).date() >= (fields.date.today() - datetime.timedelta(days=365)), sale_orders))
            groupby_dict_yr['data'] = filtered_by_yr
            for sale_order_list_yr in groupby_dict_yr['data']:
                for sale_order in sale_order_list_yr.order_line:
                    if sale_order.product_id.id == self.product_id.id:
                        total_yr = total_yr + sale_order.product_uom_qty

            self.product_sales_count_yrs = total_yr

            if self.tier.code == False:
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'out of scope')])
                self.multiplier = multiplier_list.id
            elif self.product_sales_count == '0':
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'no history')])
                self.multiplier = multiplier_list.id
            elif float(self.qty_in_stock) > (float(self.product_sales_count) * 2 ) and self.product_sales_count!='0':
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'overstocked')])
                self.multiplier = multiplier_list.id
            elif self.product_id.product_tmpl_id.premium == True:
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 'premium')])
                self.multiplier = multiplier_list.id
            elif self.tier.code == '1':
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 't1 good 45')])
                self.multiplier = multiplier_list.id
            elif self.tier.code == '2':
                multiplier_list = self.env['multiplier.multiplier'].search([('code', '=', 't2 good 35')])
                self.multiplier=multiplier_list.id

            self.cal_offer_price()
            self.expired_inventory_cal()

            self.update_product_expiration_date()


            for order in self:
                for line in order:
                    if (line.product_qty == False):
                        line.product_qty = '1'
                        line.price_subtotal = line.list_price
                        line.product_unit_price = line.list_price

            multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', self.multiplier.id)])
            possible_competition_list = self.env['competition.competition'].search([('id', '=', self.possible_competition.id)])
            self.margin = multiplier_list.margin
            self.product_unit_price=math.ceil(round(float(self.list_price) * (float(multiplier_list.retail) / 100),2))
            self.product_offer_price =math.ceil(round(float(self.product_unit_price) * (float(multiplier_list.margin) / 100 + float(possible_competition_list.margin) / 100),2))
            self.product_tier=self.product_id.tier

    def update_product_expiration_date(self):
        for order in self:
            order.env.cr.execute(
                "SELECT min(use_date), max(use_date) FROM public.stock_production_lot where product_id =" + str(
                    order.product_id.id))
            query_result = order.env.cr.dictfetchone()
            if query_result['max'] != None:
                self.expiration_date = fields.Datetime.from_string(str(query_result['max'])).date()

    def expired_inventory_cal(self):
        expired_lot_count = 0
        test_id_list = self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id)])
        for prod_lot in test_id_list:
            if prod_lot.use_date != False :
                if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                    expired_lot_count = expired_lot_count + 1

        self.expired_inventory = expired_lot_count

    @api.onchange('multiplier','product_qty')
    def cal_offer_price(self):
        if (self.state == 'ven_draft'):
            for order in self:
                for line in order:
                    multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                    line.margin=multiplier_list.margin
                    line.offer_price=round(float(line.product_qty) * float(line.product_offer_price),2)
                    line.product_retail = round(float(line.product_qty) * float(line.product_unit_price),2)
                    line.price_subtotal = round(float(line.product_qty) * float(line.product_offer_price),2)

    @api.multi
    def qty_in_stocks(self):
        domain = [
            ('product_id', '=',  self.product_id.id),
        ]
        moves = self.env['stock.move'].search(domain,limit=1)
        self.qty_in_stock=moves.product_qty


class Multiplier(models.Model):
    _name = 'multiplier.multiplier'
    _description = "Multiplier"

    name = fields.Char(string="Multiplier Name",required=True)
    code = fields.Char(string="Multiplier Code", required=True)
    retail = fields.Float('Retail %', digits=dp.get_precision('Product Unit of Measure'), required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Competition(models.Model):
    _name = 'competition.competition'
    _description = "Competition"

    name = fields.Char(string="Competition Name",required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Tier(models.Model):
    _name = 'tier.tier'
    _description = "Product Tier"

    name = fields.Char(string="Product Tier",required=True)
    code = fields.Char(string="Product Tier Code", required=True)


class ClassCode(models.Model):
    _name = 'classcode.classcode'
    _description = "Class Code"

    name=fields.Char(string="Class Code",required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tier = fields.Many2one('tier.tier', string="Tier")
    class_code = fields.Many2one('classcode.classcode', string="Class Code")
