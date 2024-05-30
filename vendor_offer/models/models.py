# -*- coding: utf-8 -*-

import datetime
import io
import logging
import re
import time
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
from dateutil.relativedelta import relativedelta

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

SUPERUSER_ID_INFO = 2

class VendorOffer(models.Model):
    _description = "Vendor Offer"
    _inherit = "purchase.order"

    vendor_offer_data = fields.Boolean()
    partner_id1 = fields.Many2one('res.partner', string='Vendor1', required=True)
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

    credit_amount_untaxed_before_qpa = fields.Monetary(string='Credit Offer Price', compute='_amount_all', readonly=True)
    credit_amount_qpq = fields.Monetary(string='Additional 3 %', compute='_amount_all', readonly=True)
    credit_amount_untaxed_after_qpa = fields.Monetary(string='After QPA', compute='_amount_all', readonly=True)
    credit_amount_qpq_flag = fields.Boolean(compute='_amount_all', readonly=True)

    billed_retail_untaxed = fields.Monetary(string='Billed Untaxed Retail', compute='_amount_all', readonly=True)
    billed_retail_total = fields.Monetary(string='Billed Retail Total', compute='_amount_all', readonly=True)
    final_billed_retail_total = fields.Monetary(string='Final Billed Retail Total', default=0, track_visibility='onchange')
    billed_offer_untaxed = fields.Monetary(string='Billed Untaxed Offer', compute='_amount_all', readonly=True)
    billed_offer_total = fields.Monetary(string='Billed Offer Total', compute='_amount_all', readonly=True)
    final_billed_offer_total = fields.Monetary(string='Final Billed Offer Total', default=0, track_visibility='onchange')

    '''show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to compute whether the validate should be shown.')'''

    offer_type = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('cashcredit', 'Cash/Credit')
    ], string='Offer Type',default='cashcredit')

    offer_type_popup = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit')
    ], string='Offer Type', default='cash')

    shipping_date = fields.Datetime(string="Shipping Date")
    delivered_date = fields.Datetime(string="Delivered Date")
    expected_date = fields.Datetime(string="Expected Date")

    notes_activity = fields.One2many('purchase.notes.activity', 'order_id', string='Notes')

    accelerator = fields.Boolean(string="Accelerator")
    ven_priority = fields.Selection([
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
    ], string='Offer Type', readonly=True, index=True, copy=False, default='ven_draft', track_visibility='onchange',
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
    arrival_date_grp = fields.Datetime(string="Arrival Date")

    super_user_email = fields.Char(compute='_email_info_user')
    vendor_cust_id = fields.Char(string="Customer ID",store=True,readonly=False)
    cash_text_pdf = fields.Char(string="",compute='_cash_text_pdf_fun')

    @api.onchange('cash_text_pdf')
    @api.depends('cash_text_pdf')
    def _cash_text_pdf_fun(self):
        for order in self:
            final_text = ''
            days = 0
            flag = True
            if order.payment_term_id:
                payment_term = self.env['account.payment.term'].search([('id', '=', order.payment_term_id.id)], limit=1)
                if payment_term.line_ids:
                    line_count = 0
                    for line in payment_term.line_ids:
                        line_count = line_count + 1
                        days = line.days
                    if line_count > 1:
                        flag = False

                if flag:
                    if days == 0:
                        order.cash_text_pdf = order.payment_term_id.name
                    else:
                        order.cash_text_pdf = ' ' + str(days) + ' ' + 'days'
                else:
                    order.cash_text_pdf = order.payment_term_id.name
            else:
                order.cash_text_pdf = None


    acq_manager_email = fields.Char(readonly=False, compute='acq_manager_detail')
    acq_manager_phone = fields.Char( readonly=False,compute='acq_manager_detail')

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def acq_manager_detail_pt(self):
        for order in self:
            if order.partner_id:
                order.acq_user_id = order.partner_id.acq_manager

    @api.onchange('acq_manager_email', 'acq_manager_phone')
    @api.depends('acq_manager_email', 'acq_manager_phone')
    def acq_manager_detail(self):
        for order in self:
            if order.partner_id:
                if not order.acq_user_id:
                    order.acq_user_id = order.partner_id.acq_manager
            if order.acq_user_id:
                order.acq_manager_email = order.acq_user_id.partner_id.email
                order.acq_manager_phone = order.acq_user_id.partner_id.phone
                if not order.acq_manager_email:
                    user = self.env['res.users'].search(
                        [('active', '=', True), ('id', '=', order._uid)])
                    order.acq_manager_email = user.partner_id.email
                    order.acq_manager_phone = user.partner_id.phone
                    if not order.acq_manager_email:
                        user = self.env['res.users'].search(
                            [('active', '=', True), ('id', '=', order._uid)])
                        order.acq_manager_email = user.partner_id.email
                        order.acq_manager_phone = user.partner_id.phone
                        if not order.acq_manager_email:
                            super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
                            order.acq_manager_email = super_user.email
                            order.acq_manager_phone = super_user.phone
            else:
                if not order.acq_manager_email:
                    user = self.env['res.users'].search(
                        [('active', '=', True), ('id', '=', order._uid)])
                    order.acq_manager_email = user.partner_id.email
                    order.acq_manager_phone = user.partner_id.phone
                    if not order.acq_manager_email:
                        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
                        order.acq_manager_email = super_user.email
                        order.acq_manager_phone = super_user.phone

    @api.onchange('vendor_cust_id')
    @api.depends('vendor_cust_id')
    def _onchange_vendor_cust_id(self):
        for order in self:
            if order.vendor_cust_id:
                user_fetch = self.env['res.partner'].search([('saleforce_ac', '=', order.vendor_cust_id), ])
                if user_fetch and user_fetch.id:
                    order.partner_id = user_fetch.id
                else:
                    order.partner_id = False
            else:
                order.partner_id = False

    @api.onchange('super_user_email')
    @api.depends('super_user_email')
    def _email_info_user(self):
        super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID_INFO), ])
        temp = self.offer_type
        self.super_user_email = super_user.email

    #@api.multi
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

    #@api.multi
    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('purchase_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

    #@api.multi
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

    #@api.multi
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
        new_po.update({
            'amount_untaxed': self.amount_untaxed,
            'amount_total': self.amount_total,
            'credit_amount_untaxed': round(self.credit_amount_untaxed, 2),
            'credit_amount_total': round(self.credit_amount_total, 2),
            'cash_amount_untaxed': self.cash_amount_untaxed,
            'cash_amount_total': self.cash_amount_untaxed
        })
        for line in new_po.order_line:
            for line1 in self.order_line:
                if line1.product_id == line.product_id:
                    line.update({
                        'price_subtotal': line1.price_subtotal,
                        'price_total': line1.price_total
                    })
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
                billed_retail_untaxed = billed_offer_untaxed = 0.0
                credit_amount_untaxed_before_qpa = 0.0
                credit_amount_untaxed_after_qpa = 0.0
                credit_amount_qpq_flag = False
                credit_amount_qpq = 0.0
                for line in order.order_line:
                    amount_tax += line.price_tax
                    cash_amount_untaxed += line.price_subtotal
                    amount_untaxed += line.price_subtotal
                    price_total += line.price_total

                    product_retail += line.product_retail
                    rt_price_tax += line.rt_price_tax
                    rt_price_total += line.rt_price_total
                    billed_retail_untaxed += line.billed_product_retail_price
                    billed_offer_untaxed += line.billed_product_offer_price

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
                flag = any(e in ['Ovation Elevate', 'Alliant Purchasing', 'SurgeryPartners'] for e in
                           list(map(lambda x: x.name, order.partner_id.category_id)))

                if product_retail > 0:
                    per_val = round((amount_untaxed / product_retail) * 100, 2)
                    per_val = per_val + 10
                    credit_amount_untaxed = product_retail * (per_val / 100)
                    credit_amount_untaxed_before_qpa = round(credit_amount_untaxed)
                    # IF Vendor Have 'QPA' tag then Extra 3% Amount Added in Credit Amount
                    if flag:
                        credit_amount_qpq_flag = True
                        credit_amount_qpq = math.ceil(credit_amount_untaxed * 0.03)
                        credit_amount_untaxed = credit_amount_untaxed + (credit_amount_untaxed * 0.03)
                        credit_amount_untaxed_after_qpa = credit_amount_untaxed

                    credit_amount_untaxed = credit_amount_untaxed_before_qpa + credit_amount_qpq
                    credit_amount_total = credit_amount_untaxed + amount_tax

                if order.import_type_ven != 'all_field_import':
                    order.update({
                        'max': round(max, 2),
                        'potential_profit_margin': abs(round(potential_profit_margin, 2)),

                        'amount_tax': amount_tax,

                        'rt_price_subtotal_amt': product_retail,
                        'rt_price_tax_amt': rt_price_tax,
                        'rt_price_total_amt': rt_price_total,
                        'credit_amount_untaxed': round(credit_amount_untaxed, 2),
                        'credit_amount_total': round(credit_amount_total, 2),
                        'cash_amount_untaxed': cash_amount_untaxed,
                        'cash_amount_total': cash_amount_untaxed + amount_tax,
                        'billed_retail_untaxed': billed_retail_untaxed,
                        'billed_offer_untaxed': billed_offer_untaxed,
                        'billed_retail_total': billed_retail_untaxed + amount_tax,
                        'billed_offer_total': billed_offer_untaxed + amount_tax ,
                        'credit_amount_qpq': round(credit_amount_qpq, 2),
                        'credit_amount_untaxed_before_qpa': round(credit_amount_untaxed_before_qpa, 2),
                        'credit_amount_untaxed_after_qpa': round(credit_amount_untaxed_after_qpa, 2),
                        'credit_amount_qpq_flag': credit_amount_qpq_flag

                    })

                    if order.offer_type and order.offer_type == 'credit':
                        order.update({
                            'amount_untaxed': round(credit_amount_untaxed, 2),
                            'amount_total': round(credit_amount_total, 2)
                        })
                    else:
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_total': price_total
                        })

                else:
                    order.update({
                        'max': round(max, 2),
                        'potential_profit_margin': abs(round(potential_profit_margin, 2)),

                        'amount_tax': amount_tax,

                        'rt_price_subtotal_amt': product_retail,
                        'rt_price_tax_amt': rt_price_tax,
                        'rt_price_total_amt': rt_price_total,
                        'credit_amount_untaxed': round(credit_amount_untaxed, 2),
                        'credit_amount_total': round(credit_amount_total, 2),
                        'cash_amount_untaxed': cash_amount_untaxed,
                        'cash_amount_total': cash_amount_untaxed + amount_tax,
                        'billed_retail_untaxed': billed_retail_untaxed,
                        'billed_offer_untaxed': billed_offer_untaxed,
                        'billed_retail_total': billed_retail_untaxed + amount_tax,
                        'billed_offer_total': billed_offer_untaxed + amount_tax,
                        'credit_amount_qpq': round(credit_amount_qpq, 2),
                        'credit_amount_untaxed_before_qpa': round(credit_amount_untaxed_before_qpa, 2),
                        'credit_amount_untaxed_after_qpa': round(credit_amount_untaxed_after_qpa, 2),
                        'credit_amount_qpq_flag': credit_amount_qpq_flag

                    })
                    if order.offer_type and order.offer_type == 'credit':
                        order.update({
                            'amount_untaxed': round(credit_amount_untaxed, 2),
                            'amount_total': round(credit_amount_total, 2)
                        })
                    else:
                        order.update({
                            'amount_untaxed': cash_amount_untaxed,
                            'amount_total': cash_amount_untaxed + amount_tax
                        })
            else:
                order.rt_price_subtotal_amt = False;
                order.rt_price_total_amt = False;
                order.rt_price_tax_amt = False;
                order.billed_retail_untaxed = False;
                order.billed_retail_total = False;
                order.billed_offer_untaxed = False;
                order.billed_offer_total = False;
                amount_untaxed = amount_tax = price_total = 0.0
                rt_price_tax = product_retail = rt_price_total = 0.0
                billed_retail_untaxed = billed_offer_untaxed = 0.0
                cash_amount_untaxed = 0.0
                credit_amount_untaxed_before_qpa = 0.0
                credit_amount_untaxed_after_qpa = 0.0
                credit_amount_qpq = 0.0
                credit_amount_qpq_flag = False
                direct_po_flag = False
                # res = super(VendorOffer, self)._amount_all()
                for line in order.order_line:
                    amount_tax += line.price_tax
                    rt_price_tax += line.rt_price_tax
                    rt_price_total += line.rt_price_total
                    product_retail += line.product_retail
                    if order.import_type_ven is False:
                        direct_po_flag = True
                        line.price_subtotal = line.product_qty * line.price_unit
                        amount_untaxed += line.product_qty * line.price_unit
                        price_total += line.price_subtotal + line.price_tax
                    else:
                        amount_untaxed += line.price_subtotal
                        price_total += line.price_total

                    cash_amount_untaxed += line.price_subtotal
                    billed_retail_untaxed += line.billed_product_retail_price
                    billed_offer_untaxed += line.billed_product_offer_price

                credit_amount_untaxed = 0
                credit_amount_total = 0

                flag = any(e in ['Ovation Elevate', 'Alliant Purchasing', 'SurgeryPartners'] for e in
                           list(map(lambda x: x.name, order.partner_id.category_id)))
                if product_retail > 0:
                    per_val = round((amount_untaxed / product_retail) * 100, 2)
                    per_val = per_val + 10
                    credit_amount_untaxed = product_retail * (per_val / 100)
                    # IF Vendor Have 'QPA' tag then Extra 3% Amount Added in Credit Amount
                    if order.import_type_ven != 'all_field_import':
                        if flag:
                            if order.create_date and (
                                    order.create_date.date() >= datetime.datetime.strptime('2023-11-28',
                                                                                           "%Y-%m-%d").date()):
                                credit_amount_qpq = math.ceil(credit_amount_untaxed * 0.03)
                                credit_amount_untaxed_before_qpa = round(credit_amount_untaxed)
                            else:
                                credit_amount_qpq = credit_amount_untaxed * 0.03
                                credit_amount_untaxed_before_qpa = credit_amount_untaxed

                            credit_amount_untaxed = credit_amount_untaxed + (credit_amount_untaxed * 0.03)
                            credit_amount_untaxed_after_qpa = credit_amount_untaxed
                            credit_amount_untaxed = credit_amount_untaxed_before_qpa + credit_amount_qpq

                    elif order.offer_type == 'credit' and flag:
                        credit_amount_qpq_flag = True
                        if order.create_date and (
                                order.create_date.date() >= datetime.datetime.strptime('2023-11-28',
                                                                                       "%Y-%m-%d").date()):
                            credit_amount_qpq = math.ceil(credit_amount_untaxed * 0.03)
                            credit_amount_untaxed_before_qpa = round(credit_amount_untaxed)
                        else:
                            credit_amount_qpq = credit_amount_untaxed * 0.03
                            credit_amount_untaxed_before_qpa = credit_amount_untaxed

                        credit_amount_untaxed = credit_amount_untaxed + (credit_amount_untaxed * 0.03)
                        credit_amount_untaxed_after_qpa = credit_amount_untaxed
                        credit_amount_untaxed = credit_amount_untaxed_before_qpa + credit_amount_qpq

                    credit_amount_total = credit_amount_untaxed + amount_tax

                order.update({
                    'amount_tax': amount_tax,

                    'rt_price_subtotal_amt': product_retail,
                    'rt_price_tax_amt': rt_price_tax,
                    'rt_price_total_amt': rt_price_total,
                    'billed_retail_untaxed': billed_retail_untaxed,
                    'billed_offer_untaxed': billed_offer_untaxed,
                    'billed_retail_total': billed_retail_untaxed + amount_tax,
                    'billed_offer_total': billed_offer_untaxed + amount_tax,
                    'credit_amount_untaxed': round(credit_amount_untaxed, 2),
                    'credit_amount_total': round(credit_amount_total, 2),
                    'cash_amount_untaxed': cash_amount_untaxed,
                    'cash_amount_total': cash_amount_untaxed + amount_tax,
                    'credit_amount_qpq': round(credit_amount_qpq, 2),
                    'credit_amount_untaxed_before_qpa': round(credit_amount_untaxed_before_qpa, 2),
                    'credit_amount_untaxed_after_qpa': round(credit_amount_untaxed_after_qpa, 2),
                    'credit_amount_qpq_flag': credit_amount_qpq_flag
                })

                #  The reason a static date is added : It is to do calculation for the records of PO
                #  which are created  after the solutions  is pushed  to production
                #  The old PO though they are showing wrong value should not be affected
                #  This is discussed with client (Bryon) and then implemented in this way .
                #  Even the old PO are showing wrong credit values CLient have handelled   it in Bills

                if order.create_date and (
                        order.create_date.date() >= datetime.datetime.strptime('2023-02-12', "%Y-%m-%d").date()):
                    if order.offer_type:
                        if order.offer_type == 'credit':
                            if order.create_date and (
                                    order.create_date.date() >= datetime.datetime.strptime('2023-11-28',
                                                                                           "%Y-%m-%d").date()):
                                # This is Amount Untaxed cal According to client request
                                # If the dollar amount is below .50 it should round down,
                                # if the dollar amount is .50 or above, it should round up to the next dollar.
                                decimal_value = round(credit_amount_untaxed, 2) - int(round(credit_amount_untaxed, 2))
                                credit_amount_untaxed_new = float(math.floor(round(credit_amount_untaxed, 2)) if decimal_value <= 0.5 else math.ceil(
                                    round(credit_amount_untaxed, 2)))
                                order.update({
                                    'amount_untaxed': credit_amount_untaxed_new,
                                    'amount_total': round(credit_amount_untaxed_new + amount_tax, 2)
                                })
                            else:
                                order.update({
                                    'amount_untaxed': math.floor(round(credit_amount_untaxed, 2)),
                                    'amount_total': math.floor(round(credit_amount_total, 2))
                                })
                        else:
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_total': price_total
                            })

                if order.create_date is False and direct_po_flag:
                    order.update({
                        'amount_untaxed': amount_untaxed,
                        'amount_total': price_total
                    })

    #@api.multi
    def action_send_offer_email(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        temp_payment_term = self.payment_term_id.name
        test = self.super_user_email
        if (temp_payment_term == False):
            temp_payment_term = '0 Days '
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = \
                ir_model_data.get_object_reference('vendor_offer', 'email_template_edi_vendor_offer_done')[1]
            else:
                template_id = \
                ir_model_data.get_object_reference('vendor_offer', 'email_template_edi_vendor_offer_done')[1]

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
            'custom_layout': "vendor_offer.mail_notification_vendor_offer",
            'force_email': True
        })

        if self.partner_id and self.partner_id.vendor_email:
            ctx['vendor_email'] = self.partner_id.vendor_email
        elif self.partner_id and self.partner_id.email:
            ctx['vendor_email'] = self.partner_id.email

        if self.acq_user_id and self.acq_user_id.partner_id and self.acq_user_id.partner_id.email:
            ctx['acq_mgr'] = self.acq_user_id.partner_id.email

        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                # lang = template._render_template(template.lang,[ctx['default_model'], ctx['default_res_id']])
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
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

    #@api.multi
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

    #@api.multi
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

    #@api.multi
    def action_button_confirm(self):
        print('in   action_button_confirm ')
        if self.env.context.get('vendor_offer_data'):

            # purchase = self.env['purchase.order'].search([('id', '=', self.id)])
            # print(purchase)
            if self.offer_type is False:
                self.offer_type = 'cash'
            if self.offer_type:
                if self.offer_type == 'credit':
                    self.amount_untaxed = round(self.credit_amount_untaxed, 2)
                    self.amount_total = round(self.credit_amount_total, 2)
                if self.offer_type == 'cash':
                    self.amount_untaxed = round(self.cash_amount_untaxed, 2)
                    self.amount_total = round(self.cash_amount_total, 2)

            self.button_confirm()
            # self.write({'state': 'purchase'})

            self.write({'status': 'purchase', 'status_ven': 'Accepted', 'accepted_date': fields.date.today()})

            if (int(self.revision) > 0):
                temp = int(self.revision) - 1
                self.revision = str(temp)


            self.env['inventory.notification.scheduler'].send_email_after_vendor_offer_conformation(self.id)

    #@api.multi
    def action_button_confirm_api_cash(self, product_id):
        # purchase = self.env['purchase.order'].search([('id', '=', product_id)])
        self.amount_untaxed = round(self.cash_amount_untaxed, 2)
        self.amount_total = round(self.cash_amount_total, 2)
        self.offer_type = 'cash'
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

        self.env['inventory.notification.scheduler'].send_email_after_vendor_offer_conformation(self.id)

    #@api.multi
    def action_button_confirm_api_credit(self, product_id):
        # purchase = self.env['purchase.order'].search([('id', '=', product_id)])

        self.offer_type = 'credit'
        self.amount_untaxed = round(self.credit_amount_untaxed, 2)
        self.amount_total = round(self.credit_amount_total, 2)

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

        self.env['inventory.notification.scheduler'].send_email_after_vendor_offer_conformation(self.id)

    #@api.multi
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

    #@api.multi
    def action_confirm_offer_both(self):

        # if self.offer_type == 'cashcredit':
        #     if self.offer_type not in ('cash','credit'):
        #         #raise ValidationError(_('Offer Type must be either "Cash" or "Credit" to Accept '))
        #         raise UserError(_('Offer Type must be either "Cash" or "Credit" not both to Accept'))


        if self.offer_type == 'cashcredit' or not self.offer_type:
            self.offer_type_popup = 'cash'
            form_view_id = self.env.ref('vendor_offer.vendor_offer_accept_popup').id
            action = {
                'type': 'ir.actions.act_window',
                'views': [(form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Offer Accept'),
                'res_model': 'purchase.order',
                'res_id': self.id,
                'domain': [('id', '=', self.id)],
                'target': 'new'
            }

            return action


        else:
            self.action_button_confirm()

    #@api.multi
    def popup_confirm_vendor_offer(self):

        if self.offer_type_popup is False:
            self.offer_type_popup = 'cash'
        if self.offer_type_popup == 'cash':
            self.action_button_confirm_api_cash(1)
        else:
            self.action_button_confirm_api_credit(1)

    #@api.multi
    def action_cancel_vendor_offer(self):

        if self.offer_type == 'cash' or (not self.offer_type) or 'cashcredit':
            self.amount_untaxed = round(self.cash_amount_untaxed, 2)
            self.amount_total = round(self.cash_amount_total, 2)
            self.offer_type = 'cash'

        if self.offer_type == 'credit' :
            self.amount_untaxed = round(self.credit_amount_untaxed, 2)
            self.amount_total = round(self.credit_amount_total, 2)
            self.offer_type = 'credit'

        self.write({'state': 'cancel'})
        self.write({'status': 'cancel'})
        self.write({'status_ven': 'Declined'})
        self.write({'declined_date': fields.date.today()})

    #@api.multi
    def action_cancel_vendor_offer_api(self, product_id):
        purchase = self.env['purchase.order'].search([('id', '=', product_id)])

        if purchase.offer_type == 'cash' or (not purchase.offer_type) or 'cashcredit':
            purchase.amount_untaxed = round(self.cash_amount_untaxed, 2)
            purchase.amount_total = round(self.cash_amount_total, 2)
            purchase.offer_type = 'cash'

        if purchase.offer_type == 'credit':
            purchase.amount_untaxed = round(self.credit_amount_untaxed, 2)
            purchase.amount_total = round(self.credit_amount_total, 2)
            purchase.offer_type = 'credit'

        purchase.button_cancel()
        purchase.write({'state': 'cancel'})
        purchase.write({'status': 'cancel'})
        purchase.write({'status_ven': 'Declined'})
        purchase.write({'declined_date': fields.date.today()})

    #@api.multi
    def button_cancel(self):
        if (self.vendor_offer_data == True):

            if self.offer_type == 'cash' or (not self.offer_type) or 'cashcredit':
                self.amount_untaxed = round(self.cash_amount_untaxed, 2)
                self.amount_total = round(self.cash_amount_total, 2)
                self.offer_type = 'cash'

            if self.offer_type == 'credit':
                self.amount_untaxed = round(self.credit_amount_untaxed, 2)
                self.amount_total = round(self.credit_amount_total, 2)
                self.offer_type = 'credit'

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
            if 'partner_id' in vals:
                fetch_id = vals['partner_id']
                user_fetch = self.env['res.partner'].search([('id', '=', fetch_id), ])
                if user_fetch:
                    vals['vendor_cust_id'] = user_fetch.saleforce_ac
            record = super(VendorOffer, self).create(vals)
            return record
        else:
            record = super(VendorOffer, self).create(vals)
            # if(self.state!='draft'):
            #     record.button_confirm()
            return record

    #@api.multi
    # def write(self, values):
    #     self.ensure_one()
    #     if (self.state == 'ven_draft' or self.state == 'ven_sent'):
    #         # Fix for revion change on send button email template
    #         if not 'message_follower_ids' in values:
    #             temp = int(self.revision) + 1
    #             values['revision'] = str(temp)
    #             values['revision_date'] = fields.Datetime.now()
    #         if 'partner_id' in values:
    #             fetch_id = values['partner_id']
    #             user_fetch = self.env['res.partner'].search([('id', '=', fetch_id), ])
    #             if user_fetch:
    #                 values['vendor_cust_id'] = user_fetch.saleforce_ac
    #         record = super(VendorOffer, self).write(values)
    #         if 'arrival_date_grp' in values:
    #             for purchase in self:
    #                 stock_pick = self.env['stock.picking'].search([('origin', '=', purchase.name)])
    #                 for pick in stock_pick:
    #                     pick.arrival_date = values['arrival_date_grp']
    #
    #         return record
    #     else:
    #         record = super(VendorOffer, self).write(values)
    #         if 'arrival_date_grp' in values:
    #             for purchase in self:
    #                 stock_pick = self.env['stock.picking'].search([('origin', '=', purchase.name)])
    #                 for pick in stock_pick:
    #                     pick.arrival_date = values['arrival_date_grp']
    #         return record

    def compute_access_url_offer(self):
        for order in self:
            auth_param = url_encode(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            temp = self.get_portal_url(query_string='&%s' % auth_param)
            access_url_vendor = '/my/vendor/%s' % (order.id)
            return access_url_vendor

    def get_mail_url(self,redirect=False):
        self.ensure_one()
        params = {}
        if hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            # ' + str(self.id) + '
        if (self.state == 'ven_draft' or self.state == 'ven_sent'):
            return '%s?%s' % ('/mail/view' if redirect else self.compute_access_url_offer(), url_encode(params))
        else:
            return '%s?%s' % ('/mail/view' if redirect else self.access_url, url_encode(params))

    #@api.multi
    def _get_share_url(self, redirect=False, signup_partner=False, pid=None, share_token=None):

        self.ensure_one()
        if self.state not in ['purchase', 'done']:
            auth_param = url_encode(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            return self.get_portal_url(query_string='&%s' % auth_param)
        return super(VendorOffer, self)._get_share_url(redirect, signup_partner, pid)


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
    uom_str = fields.Char(string="UOM")
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
            if line.env.context.get('vendor_offer_data') or line.state == 'ven_draft' or line.state == 'ven_sent':

                taxes1 = line.taxes_id.compute_all(float(line.product_unit_price), line.order_id.currency_id,
                                                   line.product_qty, product=line.product_id,
                                                   partner=line.order_id.partner_id)

                taxes = line.taxes_id.compute_all(float(line.product_offer_price), line.order_id.currency_id,
                                                  line.product_qty, product=line.product_id,
                                                  partner=line.order_id.partner_id)
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
    actual_quantity = fields.Float('Qty Available For Sale', compute="_compute_qty_available", search='_search_qty_available', compute_sudo=False, digits='Product Unit of Measure', store=True)
    actual_quantity_temp = fields.Float('Qty Available For Sale Temp', compute="_compute_qty_available_temp",
                                        store=False)

    def _compute_qty_available_temp(self):
        for template in self:
            stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', template.id)])
            reserved_quantity = 0
            if len(stock_quant) > 0:
                for lot in stock_quant:
                    if lot.lot_id and lot.lot_id.expiration_date and \
                            lot.lot_id.expiration_date.date() > datetime.datetime.now().date():
                        reserved_quantity += lot.reserved_quantity
            template.actual_quantity_temp = template.qty_available - reserved_quantity
            template.update({'actual_quantity': template.qty_available - reserved_quantity})

    def action_test_prod(self):
        start_time = time.time()
        prod_list = self.env['product.product'].search([('active', '=', True)])
        for template in prod_list:
            stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', template.id)])
            reserved_quantity = 0
            if len(stock_quant) > 0:
                for lot in stock_quant:
                    if lot.lot_id and lot.lot_id.expiration_date and \
                            lot.lot_id.expiration_date.date() > datetime.datetime.now().date():
                        reserved_quantity += lot.reserved_quantity
            cal_qty = template.qty_available - reserved_quantity
            if template.actual_quantity != cal_qty:
                template.update({'actual_quantity': cal_qty})
        print("--- %s seconds ---" % (time.time() - start_time))

    @api.depends('product_variant_ids', 'product_variant_ids.stock_quant_ids',
                 'product_variant_ids.stock_quant_ids.reserved_quantity',
                 'product_variant_ids.stock_move_ids.product_qty', 'product_variant_ids.stock_move_ids.state')
    @api.depends_context('product_id', 'company', 'location', 'warehouse')
    def _compute_qty_available(self):
        for template in self:
            stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', template.id)])
            reserved_quantity = 0
            if len(stock_quant) > 0:
                for lot in stock_quant:
                    if lot.lot_id and lot.lot_id.expiration_date and \
                            lot.lot_id.expiration_date.date() > datetime.datetime.now().date():
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


# class VendorOfferInvoice(models.Model):
#     _inherit = "account.invoice"
#
#     is_vender_offer_invoice = fields.Boolean(string='Is Vendor Offer')
#
#     @api.onchange('purchase_id')
#     def purchase_order_change(self):
#         if not self.purchase_id:
#             return {}
#         self.is_vender_offer_invoice = self.purchase_id.vendor_offer_data
#         record = super(VendorOfferInvoice, self).purchase_order_change()
#         return record


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

        # // Below method is override for sales order fedex shipping Label PO
    #@api.multi
    def fedex_send_shipping(self, pickings):
        _logger.info('Override fedex_send_shipping method call')
        res = []

        for picking in pickings:

            srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
            superself = self.sudo()
            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

            srm.transaction_detail(picking.id)

            package_type = picking.package_ids and picking.package_ids[
                0].packaging_id.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type,
                                 self.fedex_weight_unit, self.fedex_saturday_delivery)
            srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
            srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
            srm.set_recipient(picking.partner_id)

            srm.shipping_charges_payment(superself.fedex_account_number)

            srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type,
                               'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.user.company_id
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

            net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)

            # Commodities for customs declaration (international shipping)
            if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (
                    picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

                commodity_currency = order_currency
                total_commodities_amount = 0.0
                commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code

                for operation in picking.move_line_ids:
                    commodity_amount = operation.move_id.sale_line_id.price_unit or operation.product_id.list_price
                    total_commodities_amount += (commodity_amount * operation.qty_done)
                    commodity_description = operation.product_id.name
                    commodity_number_of_piece = '1'
                    commodity_weight_units = self.fedex_weight_unit
                    commodity_weight_value = self._fedex_convert_weight(
                        operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                    commodity_quantity = operation.qty_done
                    commodity_quantity_units = 'EA'
                    # DO NOT FORWARD PORT AFTER 12.0
                    if getattr(operation.product_id, 'hs_code', False):
                        commodity_harmonized_code = operation.product_id.hs_code or ''
                    else:
                        commodity_harmonized_code = ''
                    srm._commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount,
                                     commodity_number_of_piece, commodity_weight_units, commodity_weight_value,
                                     commodity_description, commodity_country_of_manufacture, commodity_quantity,
                                     commodity_quantity_units, commodity_harmonized_code)
                srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount,
                                  "NON_DOCUMENTS")
                srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id.country_id.code,
                                   superself.fedex_account_number)

            package_count = len(picking.package_ids) or 1

            # For india picking courier is not accepted without this details in label.
            po_number = dept_number = False
            if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
                po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
                dept_number = 'BILL D/T: SENDER'

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

                for sequence, package in enumerate(picking.package_ids, start=1):

                    package_weight = self._fedex_convert_weight(package.shipping_weight, self.fedex_weight_unit)
                    packaging = package.packaging_id
                    _add_customer_references_so(srm, order)
                    srm._add_package(
                        package_weight,
                        package_code=packaging.shipper_package_code,
                        package_height=packaging.height,
                        package_width=packaging.width,
                        package_length=packaging.length,
                        sequence_number=sequence,
                        po_number=po_number,
                        dept_number=dept_number,
                    )
                    srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                    request = srm.process_shipment()
                    package_name = package.name or sequence

                    warnings = request.get('warnings_message')
                    if warnings:
                        _logger.info(warnings)

                    # First package
                    if sequence == 1:
                        if not request.get('errors_message'):
                            master_tracking_id = request['master_tracking_id']
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = request['tracking_number']
                        else:
                            raise UserError(request['errors_message'])

                    # Intermediary packages
                    elif sequence > 1 and sequence < package_count:
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
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
                                company_currency = picking.company_id.currency_id
                                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                    amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())
                                else:
                                    amount = request['price']['USD']
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())

                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']

                            logmessage = _("Shipment created into Fedex<br/>"
                                           "<b>Tracking Numbers:</b> %s<br/>"
                                           "<b>Packages:</b> %s") % (
                                             carrier_tracking_ref, ','.join([pl[0] for pl in package_labels]))
                            if self.fedex_label_file_type != 'PDF':
                                attachments = [('LabelFedex-%s.%s' % (pl[0], self.fedex_label_file_type), pl[1]) for
                                               pl in package_labels]
                            if self.fedex_label_file_type == 'PDF':
                                attachments = [('LabelFedex.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
                            picking.message_post(body=logmessage, attachments=attachments)
                            shipping_data = {'exact_price': carrier_price,
                                             'tracking_number': carrier_tracking_ref}
                            res = res + [shipping_data]
                        else:
                            raise UserError(request['errors_message'])

            # TODO RIM handle if a package is not accepted (others should be deleted)

            ###############
            # One package #
            ###############
            elif package_count == 1:
                srm.add_package(net_weight)
                _add_customer_references_so(srm, order)

                # packaging = picking.package_ids[:1].packaging_id or picking.carrier_id.fedex_default_packaging_id
                # srm._add_package(
                #     net_weight,
                #     package_code=packaging.shipper_package_code,
                #     package_height=packaging.height,
                #     package_width=packaging.width,
                #     package_length=packaging.length,
                #     po_number=po_number,
                #     dept_number=dept_number,
                # )
                srm.set_master_package(net_weight, 1)

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
                        company_currency = picking.company_id.currency_id
                        if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                            amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())
                        else:
                            amount = request['price']['USD']
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())

                    carrier_tracking_ref = request['tracking_number']
                    logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (
                        carrier_tracking_ref))

                    fedex_labels = [
                        ('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
                        for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                    picking.message_post(body=logmessage, attachments=fedex_labels)

                    shipping_data = {'exact_price': carrier_price,
                                     'tracking_number': carrier_tracking_ref}
                    res = res + [shipping_data]
                else:
                    raise UserError(request['errors_message'])

            ##############
            # No package #
            ##############
            else:
                raise UserError(('No packages for this picking'))

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

 # Method added for setting value to PO for shipping label in sales order
def _add_customer_references_so(srm, order):
    if order.client_order_ref:
        srm.customer_references('P_O_NUMBER', order.client_order_ref)


def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    arrival_date = fields.Datetime(string="Arrival Date")

    @api.model
    def create(self, vals):
        record = super(StockPicking, self).create(vals)
        for pick in self:
            purchase_order = self.env['purchase.order'].search([('name', '=', pick.origin)])
            for order in purchase_order:
                if pick.arrival_date and pick.arrival_date is not None:
                    order.arrival_date_grp = pick.arrival_date
        return record

    #@api.multi
    def write(self, vals):
        record = super(StockPicking, self).write(vals)
        if 'arrival_date' in vals:
            for pick in self:
                purchase_order = self.env['purchase.order'].search([('name', '=', pick.origin)])
                for order in purchase_order:
                    if order.arrival_date_grp and (order.arrival_date_grp != vals['arrival_date']):
                        order.arrival_date_grp = vals['arrival_date']
        return record


    #@api.multi
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

    inventory_scraped_yr = fields.Char(string='Inventory Scrapped', compute='onchange_product_id_vendor_offer_pricing',
                                       readonly=True, store=False)

    average_aging = fields.Char(string='Average Aging', compute='onchange_product_id_vendor_offer_pricing',
                                    readonly=True, store=False)

    quotations_per_code = fields.Integer(string='Open Quotations Per Code',
                                         compute='onchange_product_id_vendor_offer_pricing',
                                         readonly=True, store=False)

    def onchange_product_id_vendor_offer_pricing(self):
        for line in self:
            # if line.product_tmpl_id.tier:
            #     line.product_tier = line.product_tmpl_id.tier
            result1 = {}
            if not line.id:
                return result1

            ''' sale count will show only done qty '''

            total = total_m = total_90 = total_yr = sale_total = 0
            today_date = datetime.datetime.now()
            last_3_months = fields.Date.to_string(today_date - datetime.timedelta(days=90))
            last_month = fields.Date.to_string(today_date - datetime.timedelta(days=30))
            last_yr = fields.Date.to_string(today_date - datetime.timedelta(days=365))
            #cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
            sale_order_line = self.env['sale.order.line'].search([('product_id', '=', line.id),('state', 'in',('draft', 'sent'))])
            line.quotations_per_code = len(sale_order_line)

            str_query_cm = "SELECT sum(sml.qty_done) FROM sale_order_line AS sol LEFT JOIN stock_picking AS sp ON " \
                           "sp.sale_id=sol.id " \
                           " LEFT JOIN stock_move_line AS sml ON sml.picking_id=sp.id WHERE sml.state='done' AND " \
                           "sml.location_dest_id =%s AND" \
                           " sml.product_id =%s"
            str_query_cm_new = """
                    select sum(sol.qty_delivered) from sale_order AS so JOIN sale_order_line AS sol ON
                    so.id = sol.order_id where 
                    sol.product_id = %s and sol.state in ('sale','done')
                  
            """
            str_query_total_del_qty = """
            select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) 
            as total_del_qty   from sale_order AS so JOIN sale_order_line AS sol 
            ON so.id = sol.order_id left join uom_uom AS uom on sol.product_uom=uom.id 
            where sol.product_id = %s and sol.state in ('sale','done') 
            """


            ''' state = sale condition added in all sales amount to match the value of sales amount to 
            clients PPvendorpricing file '''

            sale_all_query = """SELECT  sum(sol.price_total) as total_sales
from  product_product pp 
 INNER JOIN sale_order_line sol ON sol.product_id=pp.id 
 INNER JOIN product_template pt ON  pt.id=pp.product_tmpl_id
 INNER JOIN sale_order so ON so.id=sol.order_id
 INNER JOIN stock_picking sp ON sp.sale_id =so.id
 where pp.id =%s and sp.date_done>= %s and sp.date_done<=%s and sp.location_dest_id = 9
  group by sp.state"""

            self.env.cr.execute(sale_all_query, (line.id, last_yr,today_date))

            sales_all_value = 0
            sales_all_val = self.env.cr.fetchone()
            if sales_all_val and  sales_all_val[0] is not None:
                sales_all_value = sales_all_value + float(sales_all_val[0])
            line.amount_total_ven_pri = sales_all_value

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_3_months))
            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_3_months))

            quant_90 = self.env.cr.fetchone()
            if quant_90[0] is not None:
                total_90 = total_90 + int(quant_90[0])
            line.product_sales_count_90 = total_90

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_month))

            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_month))

            quant_m = self.env.cr.fetchone()
            if quant_m[0] is not None:
                total_m = total_m + int(quant_m[0])
            line.product_sales_count_month = total_m

            # self.env.cr.execute(str_query_cm + " AND sp.date_done>=%s", (cust_location_id,
            #                                                              line.id, last_yr))

            self.env.cr.execute(str_query_total_del_qty + " AND so.date_order>=%s", (line.id, last_yr))

            quant_yr = self.env.cr.fetchone()
            if quant_yr[0] is not None:
                total_yr = total_yr + int(quant_yr[0])
            line.product_sales_count_yrs = total_yr

            # self.env.cr.execute(str_query_cm, (cust_location_id, line.id))
            self.env.cr.execute(str_query_total_del_qty, [line.id])

            quant_all = self.env.cr.fetchone()
            if quant_all[0] is not None:
                total = total + int(quant_all[0])
            line.product_sales_count = total

            self.expired_inventory_cal(line)
            line.qty_in_stock = line.qty_available
            line.tier_name = line.tier.name

            sql_query = """SELECT     Date(PUBLIC.stock_production_lot.create_date) AS create_date , 
                                                   Sum(PUBLIC.stock_quant.quantity)              AS quantity 
                                        FROM       PUBLIC.product_product 
                                        INNER JOIN PUBLIC.product_template 
                                        ON         ( 
                                                              PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                        INNER JOIN PUBLIC.stock_production_lot 
                                        ON         ( 
                                                              PUBLIC.stock_production_lot.product_id=PUBLIC.product_product.id ) 
                                        INNER JOIN PUBLIC.stock_quant 
                                        ON         ( 
                                                              PUBLIC.stock_quant.lot_id=PUBLIC.stock_production_lot.id) 
                                        INNER JOIN PUBLIC.stock_location 
                                        ON         ( 
                                                              PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                        INNER JOIN PUBLIC.stock_warehouse 
                                        ON         ( 
                                                              PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                           PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                           wh_pack_stock_loc_id)) 
                                        WHERE      PUBLIC.stock_quant.quantity>0 
                                        AND        product_template.id = %s  AND stock_production_lot.use_date >= %s
                                        GROUP BY   PUBLIC.stock_production_lot.create_date, 
                                                   PUBLIC.product_template.id
                                                   """
            self._cr.execute(sql_query, (line.product_tmpl_id.id,today_date))
            product_lot_list = self.env.cr.dictfetchall()
            sum_qty_day = 0
            total_quantity = 0
            for obj in product_lot_list:
                date_format = "%Y-%m-%d"
                today = fields.date.today().strftime('%Y-%m-%d')
                a = datetime.datetime.strptime(str(today), date_format)
                b = datetime.datetime.strptime(str(obj['create_date']), date_format)
                diff = a - b

                total_quantity = total_quantity + obj['quantity']
                sum_qty_day = sum_qty_day + (obj['quantity'] * diff.days)

            if total_quantity > 0:
                line.average_aging = int(round(sum_qty_day / total_quantity, 0))
            else:
                line.average_aging = 0

            scrapped_list = self.env['stock.scrap'].search([('product_id', '=', line.id), ('state', '=', 'done')
                                                               , ('date_done', '>', last_yr),
                                                            ('date_done', '<', today_date)])
            total_qty = 0
            for obj in scrapped_list:
                total_qty = total_qty + obj.scrap_qty

            line.inventory_scraped_yr = int(total_qty)

    def expired_inventory_cal(self, line):
        expired_lot_count = 0
        test_id_list = self.env['stock.production.lot'].search([('product_id', '=', line.id)])
        for prod_lot in test_id_list:
            if prod_lot.use_date:
                if fields.Datetime.from_string(prod_lot.use_date).date() < fields.date.today():
                    expired_lot_count = expired_lot_count + 1

        line.expired_inventory = expired_lot_count

    #@api.multi
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
                                         'PREMIUM', 'EXP INVENTORY', 'SALES COUNT 90', 'Quantity on Order',
                                         'Average Aging', 'Inventory Scrapped','Open Quotations Per Code']))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        #company = self.env['res.company'].search([], limit=1, order="id desc")
        company = self.env.company

        # sql_fuction = """
        #                         CREATE  OR REPLACE FUNCTION get_aging_days(product_template_param integer)  RETURNS integer AS $$
        #                         DECLARE
        #                             rec RECORD;
        #                             query text;
        #                             diff  integer;
        #                             sum_qty_day integer;
        #                             total_quantity integer;
        #                             aging decimal;
        #                         BEGIN
        #                             total_quantity = 0;
        #                             sum_qty_day= 0;
        #                             aging = 0;
        #
        #                              query := 'SELECT    date_part(''day'', now() -   Date(PUBLIC.stock_production_lot.create_date) )as diff ,
        #                                                Sum(PUBLIC.stock_quant.quantity)              AS quantity
        #                                     FROM       PUBLIC.product_product
        #                                     INNER JOIN PUBLIC.product_template
        #                                     ON         (
        #                                                           PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id)
        #                                     INNER JOIN PUBLIC.stock_production_lot
        #                                     ON         (
        #                                                           PUBLIC.stock_production_lot.product_id=PUBLIC.product_product.id )
        #                                     INNER JOIN PUBLIC.stock_quant
        #                                     ON         (
        #                                                           PUBLIC.stock_quant.lot_id=PUBLIC.stock_production_lot.id)
        #                                     INNER JOIN PUBLIC.stock_location
        #                                     ON         (
        #                                                           PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id)
        #                                     INNER JOIN PUBLIC.stock_warehouse
        #                                     ON         (
        #                                                           PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id,
        #                                                                                        PUBLIC.stock_warehouse.wh_output_stock_loc_id,
        #                                                                                        wh_pack_stock_loc_id))
        #                                     WHERE      PUBLIC.stock_quant.quantity>0
        #                                     AND        product_template.id = ' || product_template_param || '
        #                                     GROUP BY   PUBLIC.stock_production_lot.create_date,
        #                                                PUBLIC.product_template.id';
        #                             FOR rec IN EXECUTE query
        #                             LOOP
        #                                 total_quantity = total_quantity + rec.quantity;
        #                                 sum_qty_day = sum_qty_day + (rec.quantity *  rec.diff);
        #
        #                             END LOOP;
        #                             IF total_quantity > 0 THEN
        #                                 aging = sum_qty_day::decimal / total_quantity;
        #                             END IF;
        #                             -- RAISE NOTICE '% - %', total_quantity, sum_qty_day;
        #                             -- RAISE NOTICE '- % -',  aging;
        #                             RETURN aging;
        #                         END;
        #                         $$ LANGUAGE plpgsql;
        #                                 """

        # WHERE  so.confirmation_date >= %s         add this fields
        str_query = """
                        SELECT pt.sku_code, 
                           pt.name, 
                           pt.list_price, 
                           pb.name AS product_brand_id, 
                           tt.name AS tier, 
                           pt.premium, 
                           pp.id, 
                           pp.product_tmpl_id ,
                           CASE 
                             WHEN exp_evntory.name IS NULL THEN '0' 
                             ELSE exp_evntory.name 
                           END     AS expired_lot_count, 
                           CASE 
                             WHEN all_sales.qty_done IS NULL THEN '0' 
                             ELSE all_sales.qty_done 
                           END     AS product_sales_count, 
                           CASE 
                             WHEN yr_sales.qty_done IS NULL THEN '0' 
                             ELSE yr_sales.qty_done 
                           END     AS product_sales_count_yrs, 
                           CASE 
                             WHEN all_sales_amount.total_sales IS NULL THEN '0' 
                             ELSE all_sales_amount.total_sales 
                           END     AS amount_total_ven_pri, 
                           CASE 
                             WHEN ninty_sales.qty_done IS NULL THEN '0' 
                             ELSE ninty_sales.qty_done 
                           END     AS product_sales_count_90,
                           CASE
                           when pt.actual_quantity IS NULL THEN '0' 
                           ELSE pt.actual_quantity end as actual_quantity,
                           CASE 
                             WHEN qty_on_order.product_qty IS NULL THEN '0' 
                             ELSE qty_on_order.product_qty 
                           END     AS qty_on_order,
                           CASE 
                             WHEN inventory_scrapped.scrap_qty IS NULL THEN '0' 
                             ELSE inventory_scrapped.scrap_qty 
                           END     AS scrap_qty ,
                           CASE 
                             WHEN aging.aging_days IS NULL THEN '0' 
                             ELSE aging.aging_days 
                           END     AS aging_days ,
                             CASE 
                             WHEN quotations_per_code.quotation_count IS NULL THEN '0' 
                             ELSE quotations_per_code.quotation_count
                           END     AS quotations_per_code
                          
                    FROM   product_product pp 
                           inner join product_template pt 
                                   ON pp.product_tmpl_id = pt.id 
                                      AND pt.TYPE = 'product' 
                           left join tier_tier tt 
                                  ON pt.tier = tt.id 
                           left join product_brand pb 
                                  ON pt.product_brand_id = pb.id 
                           left join (select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer)) 
                            AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id 
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where 
                                   sol.state in ('sale','done') 
                                  GROUP BY  sol.product_id) AS all_sales 
                                  ON pp.id = all_sales.product_id 
                           left join (SELECT CASE 
                                               WHEN Abs(SUM(sol.qty_delivered * sol.price_reduce)) IS NULL THEN 0 
                                               ELSE Abs(SUM(sol.qty_delivered * sol.price_reduce)) 
                                             END AS total_sales, 
                                             ppi.id
                                             
                                      FROM   product_product ppi 
                                             inner join sale_order_line sol 
                                                     ON sol.product_id = ppi.id  and sol.state NOT IN ('cancel','void')
                                             inner join product_template pt 
                                                     ON pt.id = ppi.product_tmpl_id 
                                             inner join sale_order so 
                                                     ON so.id = sol.order_id 
                                             INNER JOIN stock_picking sp ON sp.sale_id =so.id
                                     WHERE   sp.date_done >= %s and sp.location_dest_id = 9
                                             AND sp.state IN ('done') 
                                      GROUP  BY ppi.id) AS all_sales_amount 
                                  ON all_sales_amount.id = pp.id 
                           left join (select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer))
                            AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id  
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where 
                                   sol.state in ('sale','done')
                                   and so.date_order >= %s 
                                  GROUP BY  sol.product_id ) AS yr_sales 
                                  ON pp.id = yr_sales.product_id 
                                  
                             left join(SELECT ppc.id,count(ppc.id) as quotation_count 
                                    from  product_product ppc   
                                       INNER JOIN sale_order_line soli ON soli.product_id=ppc.id 
                                       INNER JOIN product_template pti ON  pti.id=ppc.product_tmpl_id 
                                       INNER JOIN sale_order sor ON sor.id=soli.order_id   
                                        where sor.state in ('draft','sent')   
                                           GROUP  BY ppc.id) AS quotations_per_code
                                           on pp.id =  quotations_per_code.id
                                  
                          LEFT JOIN ( 
                         select  case when sum(quantity) = 0 then 0 else round(cast (sum(sum_qty_day)/sum(quantity) as numeric),0) end   as aging_days,pt_id as pt_id  from
									( SELECT     date_part('day', now() -  Date(PUBLIC.stock_production_lot.create_date)) as diff, 
                                                       Sum(PUBLIC.stock_quant.quantity)              AS quantity ,
										Sum(PUBLIC.stock_quant.quantity)  * date_part('day', now() -  Date(PUBLIC.stock_production_lot.create_date)) as sum_qty_day,
																	PUBLIC.product_template.id	as pt_id						   
                                            FROM       PUBLIC.product_product 
                                            INNER JOIN PUBLIC.product_template 
                                            ON         ( 
                                                                  PUBLIC.product_product.product_tmpl_id = PUBLIC.product_template.id) 
                                            INNER JOIN PUBLIC.stock_production_lot 
                                            ON         ( 
                                                                  PUBLIC.stock_production_lot.product_id=PUBLIC.product_product.id ) 
                                            INNER JOIN PUBLIC.stock_quant 
                                            ON         ( 
                                                                  PUBLIC.stock_quant.lot_id=PUBLIC.stock_production_lot.id) 
                                            INNER JOIN PUBLIC.stock_location 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id=PUBLIC.stock_quant.location_id) 
                                            INNER JOIN PUBLIC.stock_warehouse 
                                            ON         ( 
                                                                  PUBLIC.stock_location.id IN (PUBLIC.stock_warehouse.lot_stock_id, 
                                                                                               PUBLIC.stock_warehouse.wh_output_stock_loc_id,
                                                                                               wh_pack_stock_loc_id)) 
                                            WHERE      PUBLIC.stock_quant.quantity>0 AND PUBLIC.stock_production_lot.use_date >= %s
                                        
                                            GROUP BY   PUBLIC.stock_production_lot.create_date, 
                                                       PUBLIC.product_template.id ) as all_rec
												
												 GROUP BY pt_id 
								) as aging  on aging.pt_id = pp.product_tmpl_id 
								
								"""

        # str_query_join_old = """
        #
        #                 LEFT JOIN
        #         (
        #                   SELECT    sum(sml.qty_done) AS qty_done,
        #                             sml.product_id
        #                   FROM      sale_order_line AS sol
        #                   LEFT JOIN stock_picking   AS sp
        #                   ON        sp.sale_id=sol.id
        #                   LEFT JOIN stock_move_line AS sml
        #                   ON        sml.picking_id=sp.id
        #                   WHERE     sml.state='done'
        #                 AND       sml.location_dest_id =%s
        #                   AND       sp.date_done >= %s
        #
        #                   GROUP BY  sml.product_id ) AS ninty_sales ON pp.id=ninty_sales.product_id LEFT JOIN
        #         (
        #                  SELECT   count(spl.NAME) AS NAME,
        #                           spl.product_id
        #                  FROM     stock_production_lot spl
        #                  WHERE    spl.use_date < %s
        #                  GROUP BY spl.product_id ) AS exp_evntory ON pp.id=exp_evntory.product_id LEFT JOIN
        #         (
        #                    SELECT     sum(sq.quantity) AS qty_available,
        #                               spl.product_id
        #                    FROM       stock_quant sq
        #                    INNER JOIN stock_production_lot AS spl
        #                    ON         sq.lot_id = spl.id
        #                    INNER JOIN stock_location AS sl
        #                    ON         sq.location_id = sl.id
        #                    WHERE      sl.usage IN ('internal',
        #                                            'transit')
        #                    GROUP BY   spl.product_id ) AS qty_available_count ON pp.id=qty_available_count.product_id LEFT JOIN
        #         (
        #                  SELECT   "stock_move"."product_id"       AS "product_id",
        #                           sum("stock_move"."product_qty") AS "product_qty"
        #                  FROM     "stock_location"                AS "stock_move__location_dest_id",
        #                           "stock_location"                AS "stock_move__location_id",
        #                           "stock_move"
        #                  WHERE    (
        #                                    "stock_move"."location_id" = "stock_move__location_id"."id"
        #                           AND      "stock_move"."location_dest_id" = "stock_move__location_dest_id"."id")
        #                  AND      ((((
        #                                                               "stock_move"."state" IN('waiting',
        #                                                                                       'confirmed',
        #                                                                                       'assigned',
        #                                                                                       'partially_available')) )
        #                                    AND      (
        #                                                      "stock_move__location_dest_id"."parent_path" :: text LIKE '1/11/%%' ))
        #                           AND      (
        #                                             NOT((
        #                                                               "stock_move__location_id"."parent_path" :: text LIKE '1/11/%%' )) ))
        #                  AND      (
        #                                    "stock_move"."company_id" IS NULL
        #                           OR       (
        #                                             "stock_move"."company_id" IN(""" + str(company.id) + """)))
        #                  GROUP BY "stock_move"."product_id" ) AS qty_on_order ON pp.id=qty_on_order.product_id LEFT JOIN
        #         (
        #                  SELECT   sum(sts.scrap_qty) AS scrap_qty,
        #                           sts.product_id
        #                  FROM     stock_scrap sts
        #                  WHERE    sts.state ='done'
        #                  AND      sts.date_done < %s
        #                  AND      sts.date_done > %s
        #                  GROUP BY sts.product_id ) AS inventory_scrapped ON pp.id=inventory_scrapped.product_id WHERE pp.active=true  """

        str_query_join = """  

                                LEFT JOIN 
                        ( 
                                   select sum(sol.qty_delivered * CAST(coalesce((1.0 / factor), '0') AS integer))
                                   AS qty_done,sol.product_id
                                   from sale_order AS so JOIN sale_order_line AS sol ON
                                   so.id = sol.order_id
                                   left join uom_uom AS uom on sol.product_uom=uom.id
                                   where 
                                   sol.state in ('sale','done')
                                   and so.date_order >= %s 
                                  GROUP BY  sol.product_id
                           ) AS ninty_sales ON pp.id=ninty_sales.product_id LEFT JOIN 
                        ( 
                                 SELECT   count(spl.NAME) AS NAME, 
                                          spl.product_id 
                                 FROM     stock_production_lot spl 
                                 WHERE    spl.use_date < %s 
                                 GROUP BY spl.product_id ) AS exp_evntory ON pp.id=exp_evntory.product_id LEFT JOIN 
                        ( 
                                   SELECT     sum(sq.quantity) AS qty_available, 
                                              spl.product_id 
                                   FROM       stock_quant sq 
                                   INNER JOIN stock_production_lot AS spl 
                                   ON         sq.lot_id = spl.id 
                                   INNER JOIN stock_location AS sl 
                                   ON         sq.location_id = sl.id 
                                   WHERE      sl.usage IN ('internal', 
                                                           'transit') 
                                   GROUP BY   spl.product_id ) AS qty_available_count ON pp.id=qty_available_count.product_id LEFT JOIN
                        ( 
                                 SELECT   "stock_move"."product_id"       AS "product_id", 
                                          sum("stock_move"."product_qty") AS "product_qty" 
                                 FROM     "stock_location"                AS "stock_move__location_dest_id", 
                                          "stock_location"                AS "stock_move__location_id", 
                                          "stock_move" 
                                 WHERE    ( 
                                                   "stock_move"."location_id" = "stock_move__location_id"."id" 
                                          AND      "stock_move"."location_dest_id" = "stock_move__location_dest_id"."id")
                                 AND      (((( 
                                                                              "stock_move"."state" IN('waiting', 
                                                                                                      'confirmed', 
                                                                                                      'assigned', 
                                                                                                      'partially_available')) )
                                                   AND      ( 
                                                                     "stock_move__location_dest_id"."parent_path" :: text LIKE '1/11/%%' ))
                                          AND      ( 
                                                            NOT(( 
                                                                              "stock_move__location_id"."parent_path" :: text LIKE '1/11/%%' )) ))
                                 AND      ( 
                                                   "stock_move"."company_id" IS NULL 
                                          OR       ( 
                                                            "stock_move"."company_id" IN(""" + str(company.id) + """))) 
                                 GROUP BY "stock_move"."product_id" ) AS qty_on_order ON pp.id=qty_on_order.product_id LEFT JOIN
                        ( 
                                 SELECT   sum(sts.scrap_qty) AS scrap_qty, 
                                          sts.product_id 
                                 FROM     stock_scrap sts 
                                 WHERE    sts.state ='done' 
                                 AND      sts.date_done < %s 
                                 AND      sts.date_done > %s 
                                 GROUP BY sts.product_id ) AS inventory_scrapped ON pp.id=inventory_scrapped.product_id WHERE pp.active=true  """

        start_time = time.time()
        #self.env.cr.execute(sql_fuction)
        # self.env.cr.execute(str_query + str_query_join, (cust_location_id,last_yr, cust_location_id, last_yr,today_date,
        #                                                  cust_location_id, last_3_months, today_date,
        #                                                  today_date, last_yr))
        self.env.cr.execute(str_query + str_query_join,
                            (last_yr, last_yr,today_date,
                             last_3_months, today_date,
                             today_date, last_yr))

        new_list = self.env.cr.dictfetchall()

        for line in new_list:
            #count = count + 1  # for printing count if needed
            # self.env.cr.execute("select get_aging_days(" + str(line['product_tmpl_id']) + ")")
            # aging_days = self.env.cr.fetchone()
            product_lines_export_pp.append(
                ([line['sku_code'], line['name'], line['list_price'], line['product_brand_id'],
                  line['tier'],line['product_sales_count'], line['product_sales_count_yrs'],
                  line['actual_quantity'], line['amount_total_ven_pri'], line['premium'],
                  line['expired_lot_count'], line['product_sales_count_90'], line['qty_on_order'],
                  line['aging_days'], line['scrap_qty'],line['quotations_per_code']]))

        print("--- %s seconds ---" % (time.time() - start_time))

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
        return 'text/csv'

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
        try:
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
            number_style = xlwt.easyxf(num_format_str='0')  # for number (for Column product Number)
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

                    if isinstance(cell_value, str):
                        cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                        # Excel supports a maximum of 32767 characters in each cell:
                        cell_value = cell_value[:32767]
                    elif isinstance(cell_value, datetime.datetime):
                        cell_style = datetime_style
                    elif isinstance(cell_value, datetime.date):
                        cell_style = date_style
                    if cell_index == 0:
                        cell_style = number_style
                    worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

            fp = io.BytesIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            return data
        except Exception as ex:
            _logger.error("Error", ex)

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



class CustomerACQManager(models.Model):
    _inherit = 'res.partner'

    acq_manager = fields.Many2one('res.users', string="ACQ Manager", domain="[('active', '=', True)"""
                                                                            ",('share','=',False)]")

    vendor_email = fields.Char(string="Vendor Email", track_visibility='onchange')

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    #@api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """ - mass_mailing: we cannot render, so return the template values
            - normal mode: return rendered values
            /!\ for x2many field, this onchange return command instead of ids
        """
        if template_id and composition_mode == 'mass_mail':
            template = self.env['mail.template'].browse(template_id)
            fields = ['subject', 'body_html', 'email_from', 'reply_to', 'mail_server_id']
            values = dict((field, getattr(template, field)) for field in fields if getattr(template, field))
            if template.attachment_ids:
                values['attachment_ids'] = [att.id for att in template.attachment_ids]
            if template.mail_server_id:
                values['mail_server_id'] = template.mail_server_id.id
            # if template.user_signature and 'body_html' in values:
            #     signature = self.env.user.signature
            #     values['body_html'] = tools.append_content_to_html(values['body_html'], signature, plaintext=False)
        elif template_id:
            #values = self.generate_email_for_composer(template_id, [res_id])[res_id]
            values = self.generate_email_for_composer(
                template_id, [res_id],
                ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to',
                 'attachment_ids', 'mail_server_id']
            )[res_id]
            # transform attachments into attachment_ids; not attached to the document because this will
            # be done further in the posting process, allowing to clean database if email not send
            attachment_ids = []
            Attachment = self.env['ir.attachment']
            for attach_fname, attach_datas in values.pop('attachments', []):
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,

                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                }
                attachment_ids.append(Attachment.create(data_attach).id)
            ship_label = self.env['ir.attachment'].search(
                [('res_id', '=', res_id), ('res_model', '=', 'purchase.order'),('name','like','%FedEx%')], order="id desc")
            if values.get('attachment_ids', []) or attachment_ids:
                #values['attachment_ids'] = [(5,)] + values.get('attachment_ids', []) + attachment_ids + ([ship_label[0].id] if ship_label else [])
                #values['attachment_ids'] = [(5,)] + values.get('attachment_ids', []) + attachment_ids
                values['attachment_ids'] = [(6, 0, values.get('attachment_ids', []) + attachment_ids + ([ship_label[0].id] if ship_label else []))]


        else:
            default_values = self.with_context(default_composition_mode=composition_mode, default_model=model,
                                               default_res_id=res_id).default_get(
                ['composition_mode', 'model', 'res_id', 'parent_id', 'partner_ids', 'subject', 'body', 'email_from',
                 'reply_to', 'attachment_ids', 'mail_server_id'])
            values = dict((key, default_values[key]) for key in
                          ['subject', 'body', 'partner_ids', 'email_from', 'reply_to', 'attachment_ids',
                           'mail_server_id'] if key in default_values)

        if values.get('body_html'):
            values['body'] = values.pop('body_html')

        # This onchange should return command instead of ids for x2many field.
        # ORM handle the assignation of command list on new onchange (api.v8),
        # this force the complete replacement of x2many field with
        # command and is compatible with onchange api.v7
        values = self._convert_to_write(values)

        return {'value': values}

