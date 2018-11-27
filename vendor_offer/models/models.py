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
    revision = fields.Char(string='Revision ')
    max = fields.Char(string='Max',  default=0)
    potential_profit_margin = fields.Char(string='Potential Profit Margin', default=0)
    accepted_date = fields.Datetime(string="Accepted Date")
    declined_date = fields.Datetime(string="Declined Date")
    retail_amt = fields.Monetary(string="Total Retail",readonly=True,default=0 ,compute='_amount_tot_all')
    offer_amount = fields.Monetary(string="Total  Offer",readonly=True,default=0,compute='_amount_tot_all')
    # date_planned = fields.Datetime(string='Scheduled Date')
    possible_competition = fields.Many2one('competition.competition', string="Possible Competition")
    rt_price_subtotal_amt = fields.Monetary(string='Subtotal', compute='_amount_tot_all')
    rt_price_total_amt = fields.Monetary( string='Total', compute='_amount_tot_all')
    rt_price_tax_amt = fields.Float(string='Tax', compute='_amount_tot_all')
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to compute whether the validate should be shown.')

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

    @api.multi
    def _compute_show_validate(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) == 1 and self.picking_count == 1:
            self.show_validate = multi.show_validate
        elif self.picking_count > 1:
            self.show_validate = True

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


    @api.onchange('order_line.product_offer_price','order_line.price_total')
    def _amount_tot_all(self):
        for order in self:
            retail_amt = offer_amount = 0.0
            rt_price_subtotal_amt_temp = rt_price_total_amt_temp =rt_price_tax_amt_temp = 0.0
            for line in order.order_line:
                retail_amt += float(line.product_retail)
                rt_price_subtotal_amt_temp+=float(line.rt_price_subtotal)
                rt_price_total_amt_temp += float(line.rt_price_total)
                rt_price_tax_amt_temp += float(line.rt_price_tax)


            order.update({
                'retail_amt': retail_amt,
                'rt_price_subtotal_amt':rt_price_subtotal_amt_temp,

                'rt_price_tax_amt': rt_price_tax_amt_temp,
                'rt_price_total_amt': rt_price_subtotal_amt_temp + rt_price_tax_amt_temp,
                'offer_amount': offer_amount,

            })

    @api.onchange('possible_competition')
    def possible_competition_onchange(self):
        self.state = 'ven_draft'
        for order in self:
            possible_competition_list = self.env['competition.competition'].search(
                [('id', '=', order.possible_competition.id)])
            for line in order.order_line:
                multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                line.margin = multiplier_list.margin
                product_unit_price_multiplier = math.ceil(
                    round(float(line.product_id.product_tmpl_id[0].list_price) * (float(multiplier_list.retail) / 100),
                          2))
                line.product_unit_price = product_unit_price_multiplier
                line.retail_price = math.ceil(round((float(line.product_qty) * float(line.product_unit_price)), 2))
                line_margin = float((float(multiplier_list.margin) / 100) + (float(possible_competition_list.margin) / 100))
                line.product_offer_price = math.ceil(round((float(product_unit_price_multiplier) * line_margin), 2))
                line.offer_price = round((float(line.product_qty) * float(line.product_offer_price)), 2)
                line.price_subtotal = line.offer_price
                # line.price_unit = line.product_offer_price

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
        '''
               This function opens a window to compose an email, with the edi purchase template message loaded by default
               '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('vendor_offer', 'email_template_edi_vendor_offer')[1]
            else:
                template_id = ir_model_data.get_object_reference('vendor_offer', 'email_template_edi_vendor_offer')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "vendor_offer.mail_template_data_notification_email_vendor_offer",
            'force_email': True
        })
        self.write({'status': 'ven_sent','state': 'ven_sent'})
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_print_vendor_offer(self):
        self.write({'status': 'ven_sent','state': 'ven_sent'})
        return self.env.ref('vendor_offer.action_report_vendor_offer').report_action(self)

    @api.multi
    def action_confirm_vendor_offer(self):
         self.write({'state': 'purchase'})
         self.write({'status': 'purchase'})
         self.write({'status_ven': 'Accepted'})
         self.write({'accepted_date': fields.date.today()})
         if (int(self.revision) > 0):
             temp = int(self.revision) - 1
             self.revision = str(temp)
         record = self.env['purchase.order']
         recordtemp = record.button_confirm()
         return recordtemp

    @api.multi
    def action_button_confirm(self):

        if (self.env.context.get('vendor_offer_data') == True):
            purchase = self.env['purchase.order'].search([('id', '=', self.id)])
            purchase.button_confirm()
            # self.write({'state': 'purchase'})
            self.write({'status': 'purchase'})
            self.write({'status_ven': 'Accepted'})
            self.write({'accepted_date': fields.date.today()})

            if (int(self.revision) > 0):
                temp = int(self.revision) - 1
                self.revision = str(temp)

    @api.multi
    def action_button_confirm_api(self,product_id):
        purchase = self.env['purchase.order'].search([('id', '=', product_id)])
        purchase.button_confirm()
        purchase.write({'status': 'purchase'})
        purchase.write({'state': 'purchase'})
        purchase.write({'status_ven': 'Accepted'})
        purchase.write({'accepted_date': fields.date.today()})
        if (int(purchase.revision) > 0):
            temp = int(purchase.revision) - 1
            purchase.revision = str(temp)


    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['ven_draft','draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def action_cancel_vendor_offer(self):
        self.write({'state': 'cancel'})
        self.write({'status': 'cancel'})
        self.write({'status_ven': 'Declined'})
        self.write({'declined_date': fields.date.today()})

    @api.multi
    def action_cancel_vendor_offer_api(self,product_id):
        purchase = self.env['purchase.order'].search([('id', '=', product_id)])
        purchase.button_cancel()
        purchase.write({'state': 'cancel'})
        purchase.write({'status': 'cancel'})
        purchase.write({'status_ven': 'Declined'})
        purchase.write({'declined_date': fields.date.today()})


    @api.multi
    def button_cancel(self):
        if (self.vendor_offer_data == True):
            self.write({'state': 'cancel'})
            self.write({'status': 'cancel'})
            self.write({'status_ven': 'Declined'})
            self.write({'accepted_date': None})
            self.write({'declined_date': fields.date.today()})
        super(VendorOffer, self).button_cancel()

    @api.model
    def create(self, vals):
        if(self.env.context.get('vendor_offer_data') == True):
            vals['state']= 'ven_draft'
            vals['vendor_offer_data']=True
            vals['revision'] = '0'
            record = super(VendorOffer, self).create(vals)
            return record
        else:
            record = super(VendorOffer, self).create(vals)
            # if(self.state!='draft'):
            #     record.button_confirm()
            return record


    @api.multi
    def write(self, values):
        if (self.state == 'ven_draft'):
            temp = int(self.revision) + 1
            values['revision'] = str(temp)
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

    rt_price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=False)
    rt_price_total = fields.Monetary(compute='_compute_amount', string='Total', store=False)
    rt_price_tax = fields.Float(compute='_compute_amount', string='Tax', store=False)


    def action_show_details(self):

        multi = self.env['stock.move'].search([('purchase_line_id', '=', self.id)])
        if len(multi) >= 1 and self.order_id.picking_count ==1:
            return multi.action_show_details()
        elif self.order_id.picking_count > 1:
            raise ValidationError(_('Picking is not possible for multiple shipping please do picking inside Shipping'))

    @api.depends('list_price', 'taxes_id','product_offer_price')
    def _compute_amount(self):
        super(VendorOfferProduct, self)._compute_amount()
        for line in self:
            if(line.state=='ven_draft'):
                multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                line.margin=multiplier_list.margin
                line.product_retail=round(float(line.product_qty) * float(line.product_unit_price),2)
                # line.price_subtotal = round(float(line.product_qty) * float(line.product_unit_price),2)
                line.price_subtotal = round(float(line.product_qty) * float(line.product_offer_price),2)
                line.update({

                    'price_subtotal': line.price_subtotal,
                })
        for line in self:
            taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)

           
            line.update({
                'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                'rt_price_total': taxes1['total_included'],
                'rt_price_subtotal': taxes1['total_excluded'],
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

            for order in self:
                for line in order:
                    line.qty_in_stock = line.product_id.qty_available

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

            self.product_unit_price= math.ceil(round(float(self.list_price) * (float(multiplier_list.retail) / 100),2))
            self.product_offer_price = math.ceil(round(float(self.product_unit_price) * (float(multiplier_list.margin) / 100 + float(possible_competition_list.margin) / 100),2))
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
            for line in self:
                multiplier_list = self.env['multiplier.multiplier'].search([('id', '=', line.multiplier.id)])
                line.margin = multiplier_list.margin
                line.price_subtotal = line.offer_price = round(
                    float(line.product_qty) * float(line.product_offer_price), 2)
                line.price_unit = line.product_offer_price
                line.product_retail = round(float(line.product_qty) * float(line.product_unit_price), 2)
                # line.price_subtotal = round(float(line.product_qty) * float(line.product_offer_price),2)


    @api.multi
    def qty_in_stocks(self):
        pass
        # domain = [
        #     ('product_id', '=',  self.product_id.id),
        # ]
        # moves = self.env['stock.quant'].search(domain,limit=1)
        # moves = self.env['stock.quant'].search([('product_id', '=', self.product_id.id), ('location_id.usage', '=', 'internal'), ('location_id.active', '=', 'true')],limit=1)
        # self.qty_in_stock=self..quantity


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
