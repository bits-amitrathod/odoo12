# -*- coding: utf-8 -*-"Hello - needed salary slip for last 3 month for Loan purpose."

import datetime
import io
import logging
import re
from random import randint

import math
from odoo import http
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import pdf
from odoo.tools import pycompat
from werkzeug.urls import url_encode

from .fedex_request import FedexRequest

_logger = logging.getLogger(__name__)
# Why using standardized ISO codes? It's way more fun to use made up codes...
# https://www.fedex.com/us/developer/WebHelp/ws/2014/dvg/WS_DVG_WebHelp/Appendix_F_Currency_Codes.htm
FEDEX_CURR_MATCH = {
    u'UYU': u'UYP',
    u'XCD': u'ECD',
    u'MXN': u'NMP',
    u'KYD': u'CID',
    u'CHF': u'SFR',
    u'GBP': u'UKL',
    u'IDR': u'RPA',
    u'DOP': u'RDD',
    u'JPY': u'JYE',
    u'KRW': u'WON',
    u'SGD': u'SID',
    u'CLP': u'CHP',
    u'JMD': u'JAD',
    u'KWD': u'KUD',
    u'AED': u'DHS',
    u'TWD': u'NTD',
    u'ARS': u'ARN',
    u'LVL': u'EURO',
}

try:
    import xlwt


    # add some sanitizations to respect the excel sheet name restrictions
    # as the sheet name is often translatable, can not control the input
    class PatchedWorkbook(xlwt.Workbook):
        def add_sheet(self, name, cell_overwrite_ok=False):
            # invalid Excel character: []:*?/\
            name = re.sub(r'[\[\]:*?/\\]', '', name)

            # maximum size is 31 characters
            name = name[:31]
            return super(PatchedWorkbook, self).add_sheet(name, cell_overwrite_ok=cell_overwrite_ok)


    xlwt.Workbook = PatchedWorkbook

except ImportError:
    xlwt = None

all_field_import = 'all_field_import'


class VendorOffer(models.Model):
    _description = "Vendor Offer"
    _inherit = "purchase.order"

    vendor_offer_data = fields.Boolean()
    status_ven = fields.Char(store=True, string="Status", copy=False)
    carrier_info = fields.Char("Carrier Info", related='partner_id.carrier_info', readonly=True)
    carrier_acc_no = fields.Char("Carrier Account No", related='partner_id.carrier_acc_no', readonly=True)
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    appraisal_no = fields.Char(string='Appraisal No#', compute="_default_appraisal_no", readonly=False, store=True)
    acq_user_id = fields.Many2one('res.users', string='Acq  Manager ')
    date_offered = fields.Datetime(string='Date Offered', default=fields.Datetime.now)
    revision = fields.Char(string='Revision ')
    revision_date = fields.Datetime(string='Revision Date')
    accepted_date = fields.Datetime(string="Accepted Date")
    declined_date = fields.Datetime(string="Declined Date")

    possible_competition = fields.Many2one('competition.competition', string="Possible Competition")
    max = fields.Char(string='Max', compute='_amount_all', default=0, readonly=True)
    potential_profit_margin = fields.Char(string='Potential Profit Margin', compute='_amount_all', default=0)
    rt_price_subtotal_amt = fields.Monetary(string='Subtotal', compute='_amount_all', readonly=True)
    rt_price_total_amt = fields.Monetary(string='Total', compute='_amount_all', readonly=True)
    rt_price_tax_amt = fields.Monetary(string='Tax', compute='_amount_all', readonly=True)
    # val_temp = fields.Char(string='Temp', default=0)
    temp_payment_term = fields.Char(string='Temp')
    offer_type_pdf_text = fields.Char(string='offer type Temp')
    credit_offer_type_pdf_text = fields.Char(string='credit offer type Temp')

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', copy=False)
    shipping_number = fields.Text(string='Tracking Reference', copy=False)

    credit_amount_untaxed = fields.Monetary(string='Untaxed Credit Offer Price', compute='_amount_all', readonly=True)
    credit_amount_total = fields.Monetary(string='Total Credit Offer Price', compute='_amount_all', readonly=True)
    cash_amount_untaxed = fields.Monetary(string='Untaxed Credit Offer Price', compute='_amount_all', readonly=True)
    cash_amount_total = fields.Monetary(string='Total Credit Offer Price', compute='_amount_all', readonly=True)

    '''show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to compute whether the validate should be shown.')'''

    offer_type = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit')
    ], string='Offer Type')

    shipping_date = fields.Datetime(string="Shipping Date")
    delivered_date = fields.Datetime(string="Delivered Date")
    expected_date = fields.Datetime(string="Expected Date")

    notes_activity = fields.One2many('purchase.notes.activity', 'order_id', string='Notes')

    accelerator = fields.Boolean(string="Accelerator")
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
    ], string='Status', readonly=True, index=True, copy=False, default='ven_draft', track_visibility='onchange',
        store=True)

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

    import_type_ven = fields.Char(string='Import Type')

    @api.multi
    def _compute_show_validate(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) == 1 and self.picking_count == 1:
            self.show_validate = multi.show_validate
        elif self.picking_count > 1:
            self.show_validate = True

    def action_validate(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) == 1 and self.picking_count == 1:
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

    @api.multi
    def action_duplicate_vendor_offer(self):
        new_po = self.copy()
        return {
            'name': 'Requests for Vendor Offer',
            'view_mode': 'form',
            'view_id': self.env.ref('vendor_offer.view_vendor_offer_form').id,
            'res_model': 'purchase.order',
            'context': "{'vendor_offer_data': True}",
            'type': 'ir.actions.act_window',
            'res_id': new_po.id,
            'target': 'main',
        }

    @api.multi
    def copy(self, default=None):
        if self.vendor_offer_data:
            self = self.with_context({'vendor_offer_data': True, 'disable_export': True})
            default = {
                'state': 'ven_draft',
                'vendor_offer_data': True,
                'revision': '1',
                'appraisal_no': 'AP' + str(randint(11111, 99999)),
                'revision_date': fields.Datetime.now()
            }
        new_po = super(VendorOffer, self).copy(default=default)
        return new_po.with_context(vendor_offer_data=True)

    @api.onchange('appraisal_no')
    def _default_appraisal_no(self):
        for order in self:
            if (order.appraisal_no == False):
                order.appraisal_no = 'AP' + str(randint(11111, 99999))

    @api.onchange('possible_competition')
    @api.depends('possible_competition')
    def _set_offer_price_temp(self):
        for order in self:
            for line in order.order_line:
                multiplier_list = line.multiplier
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

                line.update({
                    'product_offer_price': product_offer_price,
                    'product_unit_price': product_unit_price
                })

    @api.onchange('order_line.taxes_id')
    @api.depends('order_line.price_total', 'order_line.price_total', 'order_line.taxes_id',
                 'order_line.rt_price_tax', 'order_line.product_retail', 'order_line.rt_price_total')
    def _amount_all(self):
        for order in self:
            if order.env.context.get('vendor_offer_data') or order.state == 'ven_draft' or order.state == 'ven_sent':
                # if order.state == 'draft':
                #     order.state = 'ven_draft'

                amount_untaxed = amount_tax = price_total = 0.0
                rt_price_tax = product_retail = rt_price_total = potential_profit_margin = 0.0
                cash_amount_untaxed = 0.0
                for line in order.order_line:
                    amount_tax += line.price_tax
                    cash_amount_untaxed += line.price_subtotal
                    amount_untaxed += line.price_subtotal
                    price_total += line.price_total

                    product_retail += line.product_retail
                    rt_price_tax += line.rt_price_tax
                    rt_price_total += line.rt_price_total

                    # line.for_print_product_offer_price = str(line.product_offer_price)
                    # line.for_print_price_subtotal = str(line.price_subtotal)
                    # if ((line.expiration_date_str is False) or (line.expiration_date_str == '')) and line.expiration_date :
                    #     line.expiration_date_str = line.expiration_date
                    #     line.update({ 'expiration_date_str': line.expiration_date_str })

                if order.accelerator:
                    # amount_untaxed = product_retail * 0.50
                    max = rt_price_total * 0.65
                    # price_total = amount_untaxed + amount_tax
                else:
                    max = 0

                if not rt_price_total == 0:
                    potential_profit_margin = (price_total / rt_price_total * 100) - 100

                credit_amount_untaxed = 0
                credit_amount_total = 0
                if product_retail > 0:
                    per_val = round((amount_untaxed / product_retail) * 100, 2)
                    per_val = per_val+10
                    credit_amount_untaxed = product_retail * (per_val/100)
                    credit_amount_total = credit_amount_untaxed + amount_tax

                order.update({
                    'max': round(max, 2),
                    'potential_profit_margin': abs(round(potential_profit_margin, 2)),
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': price_total,
                    'rt_price_subtotal_amt': product_retail,
                    'rt_price_tax_amt': rt_price_tax,
                    'rt_price_total_amt': rt_price_total,
                    'credit_amount_untaxed': credit_amount_untaxed,
                    'credit_amount_total': credit_amount_total,
                    'cash_amount_untaxed': cash_amount_untaxed,
                    'cash_amount_total': cash_amount_untaxed + amount_tax
                })
                if order.offer_type:
                    if order.offer_type == 'credit':
                        order.update({
                            'amount_untaxed': credit_amount_untaxed,
                            'amount_total': credit_amount_total
                        })
            else:
                amount_untaxed = amount_tax = price_total = 0.0
                rt_price_tax = product_retail = rt_price_total = 0.0

                for line in order.order_line:
                    amount_tax += line.price_tax
                    rt_price_tax += line.rt_price_tax
                    rt_price_total += line.rt_price_total
                    product_retail += line.product_retail

                    order.update({
                        'amount_tax': amount_tax,
                        'rt_price_subtotal_amt': product_retail,
                        'rt_price_tax_amt': rt_price_tax,
                        'rt_price_total_amt': rt_price_total,
                    })

                super(VendorOffer, self)._amount_all()

    @api.multi
    def action_send_offer_email(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        temp_payment_term = self.payment_term_id.name
        if (temp_payment_term == False):
            temp_payment_term = '0 Days '
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
        if self.temp_payment_term != temp_payment_term or self.status != 'ven_sent':
            self.write({
                'temp_payment_term': temp_payment_term,
                'status': 'ven_sent',
                'state': 'ven_sent'}
            )
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
        self.temp_payment_term = self.payment_term_id.name
        if (self.payment_term_id.name == False):
            self.temp_payment_term = '0 Days '
        if (self.offer_type is False) or (self.offer_type == 'cash'):
            self.offer_type_pdf_text = 'Cash Back'
            self.credit_offer_type_pdf_text = ''
        elif self.offer_type == 'credit':
            self.offer_type_pdf_text = 'Credit to Purchase'
            self.credit_offer_type_pdf_text = 'Credit Offer is valid for 12 months from the date of issue'
        self.write({'status': 'ven_sent', 'state': 'ven_sent'})
        return self.env.ref('vendor_offer.action_report_vendor_offer').report_action(self)

    @api.multi
    def action_confirm_vendor_offer(self):
        self.write({
            'accepted_date': fields.date.today(),
            'status_ven': 'Accepted',
            'state': 'purchase',
            'status': 'purchase'
        })
        if int(self.revision) > 0:
            temp = int(self.revision) - 1
            self.revision = str(temp)

        return super(VendorOffer, self).button_confirm()

    @api.multi
    def action_button_confirm(self):
        print('in   action_button_confirm ')
        if self.env.context.get('vendor_offer_data'):

            # purchase = self.env['purchase.order'].search([('id', '=', self.id)])
            # print(purchase)
            self.button_confirm()
            # self.write({'state': 'purchase'})

            self.write({'status': 'purchase', 'status_ven': 'Accepted', 'accepted_date': fields.date.today()})

            if (int(self.revision) > 0):
                temp = int(self.revision) - 1
                self.revision = str(temp)

            if self.offer_type:
                if self.offer_type == 'credit':
                    self.amount_untaxed = self.credit_amount_untaxed
                    self.amount_total = self.credit_amount_total

            #self.env['inventory.notification.scheduler'].send_email_after_vendor_offer_conformation(self.id)

    @api.multi
    def action_button_confirm_api(self, product_id):
        # purchase = self.env['purchase.order'].search([('id', '=', product_id)])
        self.button_confirm()

        self.write({
            'status': 'purchase',
            'state': 'purchase',
            'status_ven': 'Accepted',
            'accepted_date': fields.date.today()
        })

        if (int(self.revision) > 0):
            temp = int(self.revision) - 1
            self.revision = str(temp)

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['ven_draft', 'draft', 'sent', 'ven_sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step'
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) or order.user_has_groups(
                'purchase.group_purchase_manager'):
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
    def action_cancel_vendor_offer_api(self, product_id):
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

        if (self.env.context.get('vendor_offer_data') == True):

            vals['state'] = 'ven_draft'
            vals['vendor_offer_data'] = True
            vals['revision'] = '1'
            vals['revision_date'] = fields.Datetime.now()

            record = super(VendorOffer, self).create(vals)
            return record
        else:
            record = super(VendorOffer, self).create(vals)
            # if(self.state!='draft'):
            #     record.button_confirm()
            return record

    @api.multi
    def write(self, values):
        if (self.state == 'ven_draft' or self.state == 'ven_sent'):
            # Fix for revion change on send button email template
            if not 'message_follower_ids' in values:
                temp = int(self.revision) + 1
                values['revision'] = str(temp)
                values['revision_date'] = fields.Datetime.now()
            record = super(VendorOffer, self).write(values)
            return record
        else:
            return super(VendorOffer, self).write(values)

    def get_mail_url(self):
        self.ensure_one()
        params = {}
        if hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            # ' + str(self.id) + '
        return '/my/vendor?' + url_encode(params)


class VendorOfferProduct(models.Model):
    _inherit = "purchase.order.line"
    _description = "Vendor Offer Product"

    product_tier = fields.Many2one('tier.tier', string="Tier", compute='onchange_product_id_vendor_offer')
    sku_code = fields.Char('Product SKU', compute='onchange_product_id_vendor_offer', store=False)
    product_brand_id = fields.Many2one('product.brand', string='Manufacture',
                                       compute='onchange_product_id_vendor_offer',
                                       help='Select a Manufacture for this product', store=False)
    product_sales_count = fields.Integer(string="Sales Count All", readonly=True,
                                         compute='onchange_product_id_vendor_offer', store=True)
    product_sales_count_month = fields.Integer(string="Sales Count Month", readonly=True,
                                               compute='onchange_product_id_vendor_offer', store=True)
    product_sales_count_90 = fields.Integer(string="Sales Count 90 Days", readonly=True,
                                            compute='onchange_product_id_vendor_offer', store=True)
    product_sales_count_yrs = fields.Integer(string="Sales Count Yr", readonly=True,
                                             compute='onchange_product_id_vendor_offer', store=True)
    qty_in_stock = fields.Integer(string="Quantity In Stock", readonly=True, compute='onchange_product_id_vendor_offer',
                                  store=True)
    expiration_date = fields.Datetime(string="Expiration Date", readonly=True, )
    expiration_date_str = fields.Char(string="Expiration Date")
    expired_inventory = fields.Char(string="Expired Inventory Items", compute='onchange_product_id_vendor_offer',
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
            total = total_m = total_90 = total_yr = 0
            str_query_cm = "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON " \
                           "sp.sale_id=sol.id " \
                           " LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND " \
                           "sml.location_dest_id =%s AND" \
                           " sml.product_id =%s"
            cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            today_date = datetime.datetime.now()
            last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))

            if line.env.context.get('vendor_offer_data') or line.state == 'ven_draft' or line.state == 'ven_sent':
                result1 = {}
                if not line.product_id:
                    return result1
                #

                #
                #     if line.import_type_ven_line == all_field_import:
                #         if 'order_list_list' in request.session:
                #             VendorOfferProduct.set_values_from_import(line)
                #
                #     else:
                ''' sale count will show only done qty '''

                last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
                last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))

                self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                             line.product_id.id, last_month))
                quant_m = self.env.cr.fetchone()
                if quant_m[0] is not None:
                    total_m = total_m + int(quant_m[0])
                line.product_sales_count_month = total_m

                self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                             line.product_id.id, last_3_months))
                quant_90 = self.env.cr.fetchone()
                if quant_90[0] is not None:
                    total_90 = total_90 + int(quant_90[0])
                line.product_sales_count_90 = total_90

                self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                             line.product_id.id, last_yr))
                quant_yr = self.env.cr.fetchone()
                if quant_yr[0] is not None:
                    total_yr = total_yr + int(quant_yr[0])
                line.product_sales_count_yrs = total_yr

                self.env.cr.execute(str_query_cm, (cust_location_id, line.product_id.id))
                quant_all = self.env.cr.fetchone()
                if quant_all[0] is not None:
                    total = total + int(quant_all[0])
                line.product_sales_count = total

                line.qty_in_stock = line.product_id.qty_available
                if line.multiplier.id == False:
                    if line.product_tier.code == False:
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'out of scope')])
                        line.multiplier = multiplier_list.id
                    elif line.product_sales_count == 0:
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'no history')])
                        line.multiplier = multiplier_list.id
                    elif float(line.qty_in_stock) > (
                            line.product_sales_count * 2) and line.product_sales_count != 0:
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'overstocked')])
                        line.multiplier = multiplier_list.id
                    elif line.product_id.product_tmpl_id.premium == True:
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 'premium')])
                        line.multiplier = multiplier_list.id
                    elif line.product_tier.code == '1':
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 't1 good 45')])
                        line.multiplier = multiplier_list.id
                    elif line.product_tier.code == '2':
                        multiplier_list = line.env['multiplier.multiplier'].search([('code', '=', 't2 good 35')])
                        line.multiplier = multiplier_list.id

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

    @api.onchange('multiplier', 'order_id.possible_competition')
    @api.depends('multiplier', 'order_id.possible_competition')
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
                'margin': margin,
                'product_unit_price': product_unit_price,
            })

    product_unit_price = fields.Monetary(string="Retail Price", default=_cal_offer_price, store=True)

    @api.onchange('multiplier', 'order_id.possible_competition')
    @api.depends('multiplier', 'order_id.possible_competition')
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

    @api.onchange('multiplier', 'order_id.possible_competition')
    @api.depends('multiplier', 'order_id.possible_competition')
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
            if line.env.context.get('vendor_offer_data') or line.state == 'ven_draft' or line.state == 'ven_sent' :


                taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                                   line.product_qty, product=line.product_id,
                                                   partner=line.order_id.partner_id)

                taxes = line.taxes_id.compute_all(float(line.product_offer_price), line.order_id.currency_id,
                                                  line.product_qty, product=line.product_id,
                                                  partner=line.order_id.partner_id)
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
                taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                                   line.product_qty, product=line.product_id,
                                                   partner=line.order_id.partner_id)
                line.update({
                    'rt_price_tax': sum(t.get('amount', 0.0) for t in taxes1.get('taxes', [])),
                    'product_retail': taxes1['total_excluded'],
                    'rt_price_total': taxes1['total_included'],
                })

                super(VendorOfferProduct, self)._compute_amount()


class Multiplier(models.Model):
    _name = 'multiplier.multiplier'
    _description = "Multiplier"

    name = fields.Char(string="Multiplier Name", required=True)
    code = fields.Char(string="Multiplier Code", required=True)
    retail = fields.Float('Retail %', digits=dp.get_precision('Product Unit of Measure'), required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Competition(models.Model):
    _name = 'competition.competition'
    _description = "Competition"

    name = fields.Char(string="Competition Name", required=True)
    margin = fields.Float('Margin %', digits=dp.get_precision('Product Unit of Measure'), required=True)


class Tier(models.Model):
    _name = 'tier.tier'
    _description = "Product Tier"

    name = fields.Char(string="Product Tier", required=True)
    code = fields.Char(string="Product Tier Code", required=True)


class ClassCode(models.Model):
    _name = 'classcode.classcode'
    _description = "Class Code"

    name = fields.Char(string="Class Code", required=True)


class ProductTemplateTire(models.Model):
    _inherit = 'product.template'

    tier = fields.Many2one('tier.tier', string="Tier")
    class_code = fields.Many2one('classcode.classcode', string="Class Code")
    actual_quantity = fields.Float(string='Qty Available For Sale', digits=dp.get_precision('Product Unit of Measure'),
                                   compute="_compute_qty_available", store=True)

    @api.depends('product_variant_ids.stock_quant_ids.reserved_quantity',
                 'product_variant_ids.stock_move_ids.remaining_qty')
    def _compute_qty_available(self):
        for template in self:

            stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', template.id)])
            reserved_quantity = 0
            if len(stock_quant) > 0:
                for lot in stock_quant:
                    reserved_quantity += lot.reserved_quantity

            template.update({'actual_quantity': template.qty_available - reserved_quantity})
            # print("---------------template -------------------------")
            # print(template)
            # print(template.actual_quantity)

    @api.model
    def create(self, vals):

        if 'tier' in vals and not vals['tier']:
            vals['tier'] = 2

        return super(ProductTemplateTire, self).create(vals)


class StockInventoryActionDone(models.Model):
    _inherit = 'stock.inventory'

    def action_done(self):
        super(StockInventoryActionDone, self).action_done()
        for item in self:
            product = item.product_id.product_tmpl_id
            product._compute_quantities()
            product._compute_qty_available()


# class SaleOrderConfirm(models.Model):
#     _inherit = 'sale.order'
#
#     def action_confirm(self):
#         super(SaleOrderConfirm, self).action_confirm()
#         for order in self.order_line:
#             order.product_id.product_tmpl_id._compute_quantities()


# ------------------ NOTE ACTIVITY -----------------

class ProductNotesActivity(models.Model):
    _name = 'purchase.notes.activity'
    _description = "Purchase Notes Activity"
    _order = 'id desc'

    order_id = fields.Many2one('purchase.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')
    note = fields.Text(string="Note", required=True)
    note_date = fields.Datetime(string="Note Date", default=fields.Datetime.now, )


class VendorOfferInvoice(models.Model):
    _inherit = "account.invoice"

    is_vender_offer_invoice = fields.Boolean(string='Is Vendor Offer')

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        self.is_vender_offer_invoice = self.purchase_id.vendor_offer_data
        record = super(VendorOfferInvoice, self).purchase_order_change()
        return record


class FedexDelivery(models.Model):
    _inherit = 'delivery.carrier'

    def fedex_send_shipping_label(self, order, popup):
        res = []
        srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)
        srm.transaction_detail(order.id)
        package_type = popup.product_packaging.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
        srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit,
                             self.fedex_saturday_delivery)
        srm.shipment_request_email(order)
        srm.set_currency(_convert_curr_iso_fdx(order.currency_id.name))
        srm.set_shipper(order.partner_id, order.partner_id)
        # srm.set_recipient(order.company_id.partner_id)
        super_user = self.env['res.users'].browse(1)
        # print(super_user.partner_id.name)
        srm.set_recipient(super_user.partner_id)
        srm.shipping_charges_payment(superself.fedex_account_number)
        srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type,
                           'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
        order_currency = order.currency_id
        net_weight = _convert_weight(popup.weight, 'LB')

        # Commodities for customs declaration (international shipping)
        if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (
                order.partner_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'):
            commodity_currency = order_currency
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = order.company_id.partner_id.country_id.code

            '''for operation in picking.move_line_ids:
                commodity_amount = order_currency.compute(operation.product_id.list_price, commodity_currency)
                total_commodities_amount += (commodity_amount * operation.qty_done)
                commodity_description = operation.product_id.name
                commodity_number_of_piece = '1'
                commodity_weight_units = self.fedex_weight_unit
                commodity_weight_value = _convert_weight(operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                commodity_quantity = operation.qty_done
                commodity_quantity_units = 'EA'
            srm.commodities(_convert_curr_iso_fdx(currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units)
            #srm.commodities(_convert_curr_iso_fdx('LB'), 0, '1',
                            'LB', 10, 'test',
                            commodity_country_of_manufacture, 1, 'EA')'''
            srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.company_id.partner_id.country_id.code, superself.fedex_account_number)

        package_count = popup.package_count

        # TODO RIM master: factorize the following crap

        ################
        # Multipackage #
        ################
        if package_count > 1:
            # Note: Fedex has a complex multi-piece shipping interface
            # - Each package has to be sent in a separate request
            # - First package is called "master" package and holds shipping-
            #   related information, including addresses, customs...
            # - Last package responses contains shipping price and code
            # - If a problem happens with a package, every previous package
            #   of the shipping has to be cancelled separately
            # (Why doing it in a simple way when the complex way exists??)

            master_tracking_id = False
            package_labels = []
            carrier_tracking_ref = ""

            for sequence in range(1, package_count + 1):
                package_weight = _convert_weight(popup.weight, self.fedex_weight_unit)
                srm.add_package(package_weight, sequence_number=sequence)
                _add_customer_references(srm, order)
                srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                request = srm.process_shipment()
                package_name = sequence

                warnings = request.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                # First package
                if sequence == 1:
                    if not request.get('errors_message'):
                        master_tracking_id = request['master_tracking_id']
                        package_labels.append((package_name, srm.get_label()))
                        carrier_tracking_ref = request['tracking_number']
                        print("first")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

                # Intermediary packages
                elif sequence > 1 and sequence < package_count:
                    if not request.get('errors_message'):
                        package_labels.append((package_name, srm.get_label()))
                        carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        print("Intermediary packages")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

                # Last package
                elif sequence == package_count:
                    # recuperer le label pdf
                    if not request.get('errors_message'):
                        package_labels.append((package_name, srm.get_label()))

                        if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                            carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                        else:
                            _logger.info("Preferred currency has not been found in FedEx response")
                            company_currency = order.company_id.currency_id
                            if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                carrier_price = company_currency.compute(
                                    request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                            else:
                                carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                        carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        order.update({
                            'carrier_id': self,
                            'shipping_number': carrier_tracking_ref.replace(request['master_tracking_id'], request['master_tracking_id']+'*')
                        })

                        logmessage = _("Shipment created into Fedex<br/>"
                                       "<b>Tracking Numbers:</b> %s<br/>"
                                       "<b>Packages:</b> %s") % (
                                         carrier_tracking_ref, ','.join([str(pl[0]) for pl in package_labels]))
                        if self.fedex_label_file_type != 'PDF':
                            attachments = [('FedEx_Label-%s-%s.%s' % (self.fedex_service_type,order.name, self.fedex_label_file_type), pl[1]) for pl in
                                           package_labels]
                        if self.fedex_label_file_type == 'PDF':
                            attachments = [('FedEx_Label-%s-%s.%s' % (self.fedex_service_type,order.name, self.fedex_label_file_type), pdf.merge_pdf([pl[1] for pl in package_labels]))]
                        order.message_post(body=logmessage, attachments=attachments)
                        shipping_data = {'exact_price': carrier_price,
                                         'tracking_number': carrier_tracking_ref}
                        res = res + [shipping_data]
                        print("Last package")
                        print(carrier_tracking_ref)
                    else:
                        raise UserError(request['errors_message'])

        # TODO RIM handle if a package is not accepted (others should be deleted)

        ###############
        # One package #
        ###############
        elif package_count == 1:

            srm.add_package(net_weight)
            srm.set_master_package(net_weight, 1)
            _add_customer_references(srm, order)

            # Ask the shipping to fedex
            request = srm.process_shipment()

            warnings = request.get('warnings_message')
            if warnings:
                _logger.info(warnings)

            if not request.get('errors_message'):

                if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                    carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                else:
                    _logger.info("Preferred currency has not been found in FedEx response")
                    company_currency = order.company_id.currency_id
                    if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                        carrier_price = company_currency.compute(
                            request['price'][_convert_curr_iso_fdx(company_currency.name)], order_currency)
                    else:
                        carrier_price = company_currency.compute(request['price']['USD'], order_currency)

                carrier_tracking_ref = request['tracking_number']
                order.update({
                    'carrier_id': self,
                    'shipping_number': carrier_tracking_ref
                })
                logmessage = (
                        _("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))

                fedex_labels = [
                    ('FedEx_Label-%s-%s-%s.%s' % (self.fedex_service_type,order.name, index, self.fedex_label_file_type), label)
                    for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                order.message_post(body=logmessage, attachments=fedex_labels)

                shipping_data = {'exact_price': carrier_price,
                                 'tracking_number': carrier_tracking_ref}
                res = res + [shipping_data]
            else:
                raise UserError(request['errors_message'])

        ##############
        # No package #
        ##############
        else:
            raise UserError(_('Please provide packages count'))
        return res


def _convert_weight(weight, unit='KG'):
    ''' Convert picking weight (always expressed in KG) into the specified unit '''
    if unit == 'KG':
        return weight
    elif unit == 'LB':
        return weight / 0.45359237
    else:
        raise ValueError


def _add_customer_references(srm, order):
    srm.customer_references('P_O_NUMBER', order.name)
    if order.acq_user_id.id:
        srm.customer_references('CUSTOMER_REFERENCE', order.acq_user_id.name)


def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def send_to_shipper(self):
        self.ensure_one()
        res = self.carrier_id.send_shipping(self)[0]
        if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
            res['exact_price'] = 0.0
        self.carrier_price = res['exact_price']
        if res['tracking_number']:
            self.carrier_tracking_ref = res['tracking_number']
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        msg = _("Shipment sent to carrier %s for shipping with tracking number %s<br/>Cost: %.2f %s") % (
            self.carrier_id.name, self.carrier_tracking_ref, self.carrier_price, order_currency.name)
        self.message_post(body=msg)


class VendorPricingList(models.Model):
    _inherit = 'product.product'

    product_sales_count = fields.Integer(string="SALES COUNT", readonly=True,
                                         compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_month = fields.Integer(string="Sales Count Month", readonly=True,
                                               compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_90 = fields.Integer(string="SALES COUNT 90", readonly=True,
                                            compute='onchange_product_id_vendor_offer_pricing', store=False)
    product_sales_count_yrs = fields.Integer(string="SALES COUNT YR", readonly=True,
                                             compute='onchange_product_id_vendor_offer_pricing', store=False)
    qty_in_stock = fields.Integer(string="QTY IN STOCK", readonly=True,
                                  compute='onchange_product_id_vendor_offer_pricing',
                                  store=False)
    expired_inventory = fields.Char(string="EXP INVENTORY", compute='onchange_product_id_vendor_offer_pricing',
                                    readonly=True,
                                    store=False)
    tier_name = fields.Char(string="TIER", readonly=True,
                            compute='onchange_product_id_vendor_offer_pricing',
                            store=False)
    amount_total_ven_pri = fields.Monetary(string='SALES TOTAL', compute='onchange_product_id_vendor_offer_pricing',
                                           readonly=True, store=False)

    def onchange_product_id_vendor_offer_pricing(self):
        for line in self:
            line.product_tier = line.product_tmpl_id.tier
            result1 = {}
            if not line.id:
                return result1

            ''' sale count will show only done qty '''

            total = total_m = total_90 = total_yr = sale_total = 0
            today_date = datetime.datetime.now()
            last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
            last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))
            last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
            cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            str_query_cm = "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON " \
                           "sp.sale_id=sol.id " \
                           " LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND " \
                           "sml.location_dest_id =%s AND" \
                           " sml.product_id =%s"

            ''' state = sale condition added in all sales amount to match the value of sales amount to 
            clients PPvendorpricing file '''

            sale_all_query = "SELECT  sum(sol.price_total) as total_sales " \
                             "                   from  product_product pp   " \
                             "                    INNER JOIN sale_order_line sol ON sol.product_id=pp.id " \
                             "                    INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id " \
                             "                    INNER JOIN sale_order so ON so.id=sol.order_id   " \
                             "        where pp.id =%s and so.confirmation_date>= %s   	and so.state in ('sale')"

            self.env.cr.execute(sale_all_query, (line.id, last_yr))

            sales_all_value = 0
            sales_all_val = self.env.cr.fetchone()
            if sales_all_val[0] is not None:
                sales_all_value = sales_all_value + float(sales_all_val[0])
            line.amount_total_ven_pri = sales_all_value

            self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                         line.id, last_3_months))
            quant_90 = self.env.cr.fetchone()
            if quant_90[0] is not None:
                total_90 = total_90 + int(quant_90[0])
            line.product_sales_count_90 = total_90

            self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                         line.id, last_month))
            quant_m = self.env.cr.fetchone()
            if quant_m[0] is not None:
                total_m = total_m + int(quant_m[0])
            line.product_sales_count_month = total_m

            self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
                                                                         line.id, last_yr))
            quant_yr = self.env.cr.fetchone()
            if quant_yr[0] is not None:
                total_yr = total_yr + int(quant_yr[0])
            line.product_sales_count_yrs = total_yr

            self.env.cr.execute(str_query_cm, (cust_location_id, line.id))
            quant_all = self.env.cr.fetchone()
            if quant_all[0] is not None:
                total = total + int(quant_all[0])
            line.product_sales_count = total

            self.expired_inventory_cal(line)
            line.qty_in_stock = line.qty_available
            line.tier_name = line.tier.name

    def expired_inventory_cal(self, line):
        expired_lot_count = 0
        test_id_list = self.env['stock.production.lot'].search([('product_id', '=', line.id)])
        for prod_lot in test_id_list:
            if prod_lot.use_date:
                if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                    expired_lot_count = expired_lot_count + 1

        line.expired_inventory = expired_lot_count

    @api.multi
    def return_tree_vendor_pri(self):
        tree_view_id = self.env.ref('vendor_offer.vendor_pricing_list').id
        action = {
            'name': 'Vendor Pricing',
            'view_mode': 'tree',
            'views': [(tree_view_id, 'tree')],
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }
        return action


#  this global variable is required for storing and fetching values as the list cant be sent using the URL,
#  and the method of ExportPPVendorPricing class will be called from JS file .
product_lines_export_pp = []


class VendorPricingExport(models.TransientModel):
    _name = 'vendor.pricing'
    _description = 'vendor pricing'

    def get_excel_data_vendor_pricing(self):
        today_date = datetime.datetime.now()
        last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
        last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
        count = 0
        product_lines_export_pp.append((['ProductNumber', 'ProductDescription', 'Price', 'CFP-Manufacturer', 'TIER',
                                         'SALES COUNT', 'SALES COUNT YR', 'QTY IN STOCK', 'SALES TOTAL',
                                         'PREMIUM', 'EXP INVENTORY', 'SALES COUNT 90']))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id

        str_query = " select pt.sku_code,pt.name,pt.list_price ,pb.name as product_brand_id ,tt.name as tier," \
                    " pt.premium ,pp.id,  " \
                    " case when exp_evntory.name is NULL THEN '0' ELSE  exp_evntory.name END " \
                    " as expired_lot_count, " \
                    " case when all_sales.qty_done  is NULL THEN '0' ELSE all_sales.qty_done END  " \
                    " as product_sales_count , " \
                    " case when yr_sales.qty_done is NULL THEN '0' ELSE yr_sales.qty_done END  " \
                    " as product_sales_count_yrs , " \
                    " case when all_sales_amount.total_sales  is NULL THEN '0' ELSE all_sales_amount.total_sales END " \
                    " as amount_total_ven_pri , " \
                    " case when ninty_sales.qty_done  is NULL THEN '0' ELSE ninty_sales.qty_done END  " \
                    " as product_sales_count_90 , " \
                    " qty_available_count.qty_available " \
                    " from product_product pp inner join product_template pt " \
                    " on pp.product_tmpl_id=pt.id and pt.type='product' " \
                    " left join tier_tier tt on   pt.tier=tt.id " \
                    " left join product_brand pb on pt.product_brand_id = pb.id " \
                    " left join " \
                    "            ( " \
                    "            select sum(sml.qty_done) as qty_done ,sml.product_id " \
                    "            FROM sale_order_line AS sol " \
                    "            LEFT JOIN stock_picking AS sp " \
                    "            ON  sp.sale_id=sol.id " \
                    "            LEFT JOIN stock_move_line AS sml " \
                    "            ON sml.picking_id=sp.id " \
                    "            WHERE sml.state='done' AND sml.location_dest_id =%s " \
                    "            group by sml.product_id " \
                    "            ) " \
                    "            as all_sales " \
                    "            on pp.id=all_sales.product_id " \
                    " left join " \
                    "        ( " \
                    "          SELECT " \
                    "        case when abs(sum(sol.price_total)) is NULL then 0 else  abs(sum(sol.price_total)) end  " \
                    "        as total_sales,ppi.id " \
                    "        from  product_product ppi " \
                    "                          INNER JOIN sale_order_line sol ON sol.product_id=ppi.id " \
                    "                          INNER JOIN product_template pt ON  pt.id=ppi.product_tmpl_id " \
                    "                          INNER JOIN sale_order so ON so.id=sol.order_id " \
                    "        where so.confirmation_date >= %s " \
                    "        and so.state in ('sale')   group by ppi.id " \
                    "         ) " \
                    "         as all_sales_amount " \
                    "         on all_sales_amount.id=pp.id  " \
                    "  left join " \
                    "         ( " \
                    "         select sum(sml.qty_done) as qty_done,sml.product_id " \
                    "         FROM sale_order_line AS sol " \
                    "         LEFT JOIN stock_picking AS sp " \
                    "         ON  sp.sale_id=sol.id " \
                    "         LEFT JOIN stock_move_line AS sml " \
                    "         ON sml.picking_id=sp.id " \
                    "         WHERE sml.state='done' AND sml.location_dest_id =%s " \
                    "        AND  sp.date_done >=  %s " \
                    "         group by sml.product_id " \
                    "         ) " \
                    "         as yr_sales " \
                    "         on pp.id=yr_sales.product_id "

        str_query_join = "  left join " \
                         "         ( " \
                         "          select sum(sml.qty_done) as qty_done,sml.product_id " \
                         "          FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp " \
                         "          ON  sp.sale_id=sol.id " \
                         "          LEFT JOIN stock_move_line AS sml " \
                         "          ON sml.picking_id=sp.id " \
                         "          WHERE sml.state='done' AND sml.location_dest_id =%s " \
                         "         AND  sp.date_done >= %s " \
                         "          group by sml.product_id " \
                         "          ) " \
                         "         as ninty_sales " \
                         "         on pp.id=ninty_sales.product_id " \
                         "  left join " \
                         "         ( " \
                         "          select count(spl.name) as name,spl.product_id from stock_production_lot spl " \
                         "          where spl.use_date < %s  group by spl.product_id " \
                         "          ) " \
                         "          as exp_evntory " \
                         "          on pp.id=exp_evntory.product_id " \
                         "  left join " \
                         "          ( " \
                         "           SELECT sum(sq.quantity) as qty_available,spl.product_id FROM stock_quant sq " \
                         "           INNER JOIN stock_production_lot as spl    ON  sq.lot_id = spl.id " \
                         "           INNER JOIN stock_location as sl ON  sq.location_id = sl.id " \
                         "           WHERE sl.usage in ('internal', 'transit') " \
                         "           group by spl.product_id " \
                         "          ) " \
                         "           as qty_available_count " \
                         "           on pp.id=qty_available_count.product_id " \
                         "                        where  pp.active=True "

        self.env.cr.execute(str_query + str_query_join, (cust_location_id, last_yr, cust_location_id, last_yr,
                                                         cust_location_id, last_3_months, today_date))
        new_list = self.env.cr.dictfetchall()

        for line in new_list:
            count = count + 1  # for printing count if needed
            product_lines_export_pp.append(
                ([line['sku_code'], line['name'], line['list_price'], line['product_brand_id'],
                  line['tier'], line['product_sales_count'], line['product_sales_count_yrs'],
                  line['qty_available'], line['amount_total_ven_pri'], line['premium'],
                  line['expired_lot_count'], line['product_sales_count_90']]))

        ''' code for writing csv file in default location in odoo 

        with open(file_name, 'w', newline='') as fp:
            a = csv.writer(fp, delimiter=',')
            data_lines = product_lines
            a.writerows(data_lines)
        print('---------- time required ----------')
        print(datetime.datetime.now() - today_date)  '''

        return product_lines_export_pp

    def download_excel_ven_price(self):
        list_val = self.get_excel_data_vendor_pricing()
        if list_val and len(list_val) > 0:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/PPVendorPricing/download_document_xl',
                'target': 'new'
            }
        else:
            product_lines_export_pp.clear()
            raise UserError(
                _('Cannot Export at the moment ,Please try after sometime.'))


class ExportPPVendorPricingCSV(http.Controller):

    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   Only CSV will be exported as per requirement

    @property
    def content_type(self):
        return 'text/csv;charset=utf8'

    def filename(self):

        #  code for custom date in file name if required
        #
        #                str_date = today_date.strftime("%m_%d_%Y_%H_%M_%S")
        #                file_name = 'PPVendorPricing_' + str_date + '.csv'
        #
        #

        #   Only CSV will be exported as per requirement
        return 'PPVendorPricing' + '.csv'

    def from_data(self, rows):
        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1)
        for data in rows:
            row = []
            for d in data:
                if isinstance(d, pycompat.string_types) and d.startswith(('=', '-', '+')):
                    d = "'" + d

                row.append(pycompat.to_text(d))
            writer.writerow(row)

        return fp.getvalue()

    @http.route('/web/PPVendorPricing/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self, token=1, debug=1):

        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added

        res = request.make_response(self.from_data(product_lines_export_pp),
                                    headers=[('Content-Disposition',
                                              content_disposition(self.filename())),
                                             ('Content-Type', self.content_type)],
                                    )
        product_lines_export_pp.clear()
        return res


class ExportPPVendorPricingXL(http.Controller):

    #   Custom code for fast export , existing code uses ORM ,so it is slow
    #   XL will be

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self):

        #  code for custom date in file name if required
        #
        #                str_date = today_date.strftime("%m_%d_%Y_%H_%M_%S")
        #                file_name = 'PPVendorPricing_' + str_date + '.xls'
        #
        #

        #   XL will be exported
        return 'PPVendorPricing' + '.xls'

    def from_data(self, field, rows):
        if len(rows) > 65535:
            raise UserError(_(
                'There are too many rows (%s rows, limit: 65535) to export as Excel 97-2003 (.xls) format. Consider splitting the export.') % len(
                rows))

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        for i, fieldname in enumerate(field):
            worksheet.write(0, i, fieldname)
            if i == 1:
                worksheet.col(i).width = 20000  #
            else:
                worksheet.col(i).width = 4000  # around 110 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style

                if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
                    # because xls uses raw export, we can get a bytes object
                    # here. xlwt does not support bytes values in Python 3 ->
                    # assume this is base64 and decode to a string, if this
                    # fails note that you can't export
                    try:
                        cell_value = pycompat.to_text(cell_value)
                    except UnicodeDecodeError:
                        raise UserError(_(
                            "Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") %
                                        fields[cell_index])

                if isinstance(cell_value, pycompat.string_types):
                    cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                    # Excel supports a maximum of 32767 characters in each cell:
                    cell_value = cell_value[:32767]
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    @http.route('/web/PPVendorPricing/download_document_xl', type='http', auth="public")
    @serialize_exception
    def download_document_xl(self, token=1, debug=1):

        #  token=1,debug=1   are added if the URL contains extra parameters , which in some case URL does contain
        #  code will produce error if the parameters are not provided so default are added
        try:
            res = request.make_response(self.from_data(product_lines_export_pp[0], product_lines_export_pp[1:]),
                                        headers=[('Content-Disposition',
                                                  content_disposition(self.filename())),
                                                 ('Content-Type', self.content_type)],
                                        )
            product_lines_export_pp.clear()
            return res

        except:
            res = request.make_response('','')
            product_lines_export_pp.clear()
            return res
