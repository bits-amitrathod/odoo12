# -*- coding: utf-8 -*-

import datetime
import logging
from random import randint

import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)

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
    final_billed_retail_total = fields.Monetary(string='Final Billed Retail Total', default=0, tracking=True)
    billed_offer_untaxed = fields.Monetary(string='Billed Untaxed Offer', compute='_amount_all', readonly=True)
    billed_offer_total = fields.Monetary(string='Billed Offer Total', compute='_amount_all', readonly=True)
    final_billed_offer_total = fields.Monetary(string='Final Billed Offer Total', default=0, tracking=True)



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
    ], string='Offer Type', readonly=True, index=True, copy=False, default='ven_draft', tracking=True,
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
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    import_type_ven = fields.Char(string='Import Type')
    arrival_date_grp = fields.Datetime(string="Arrival Date")

    super_user_email = fields.Char(compute='_email_info_user')
    vendor_cust_id = fields.Char(string="Customer ID",store=True,readonly=False)
    cash_text_pdf = fields.Char(string="",compute='_cash_text_pdf_fun')
    offer_expired = fields.Boolean(string='Offer Expired ?')
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
        # for order in self:
        #     if (order.appraisal_no == False):
        #         order.appraisal_no = 'AP' + str(randint(11111, 99999))

        for order in self:
            if not order.appraisal_no:
                while True:
                    number_str = 'AP' + str(randint(111111, 999999))
                    query_str = 'SELECT count(*) FROM purchase_order WHERE appraisal_no LIKE %s'
                    self.env.cr.execute(query_str,[number_str])
                    if 0 == self._cr.fetchone()[0]:
                        order.appraisal_no = number_str
                        break
            else:
                query_str = 'SELECT count(*) FROM purchase_order WHERE appraisal_no LIKE %s'
                self.env.cr.execute(query_str, [order.appraisal_no])
                if 0 != self._cr.fetchone()[0]:
                    raise ValidationError(_('Appraisal No# Already Exist'))


    @api.onchange('order_line.taxes_id')
    @api.depends('order_line.price_total', 'order_line.price_total', 'order_line.taxes_id',
                 'order_line.rt_price_tax', 'order_line.product_retail', 'order_line.rt_price_total')
    def _amount_all(self):
        for order in self:
            if order.env.context.get('vendor_offer_data') or order.state == 'ven_draft' or order.state == 'ven_sent':

                amount_untaxed = amount_tax = price_total = 0.0
                rt_price_tax = 0.0
                product_retail = 0.0
                rt_price_total = 0.0
                potential_profit_margin = 0.0
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
                    if (line.product_retail == 0) and line.product_qty != 0:
                        line.product_retail = line.product_qty * line.product_unit_price
                    product_retail += line.product_retail
                    rt_price_tax += line.rt_price_tax
                    if line.rt_price_total == 0:
                        line.rt_price_total = line.product_retail
                    rt_price_total += line.rt_price_total
                    billed_retail_untaxed += line.billed_product_retail_price
                    billed_offer_untaxed += line.billed_product_offer_price

                    line.for_print_product_offer_price = str(line.product_offer_price)
                    line.for_print_price_subtotal = str(line.price_subtotal)
                    if ((line.expiration_date_str is False) or (line.expiration_date_str == '')) and line.expiration_date :
                        line.expiration_date_str = line.expiration_date
                        line.update({'expiration_date_str': line.expiration_date_str})

                max = rt_price_total * 0.65 if order.accelerator else 0

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

                if order.import_type_ven not in ('all_field_import', 'new_appraisal'):
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
                rt_price_tax = 0.0
                product_retail = 0.0
                rt_price_total = 0.0
                potential_profit_margin = 0.0
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
                max = rt_price_total * 0.65 if order.accelerator else 0

                if not rt_price_total == 0:
                    potential_profit_margin = (price_total / rt_price_total * 100) - 100

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
                    'max': round(max, 2),
                    'amount_tax': amount_tax,
                    'potential_profit_margin': abs(round(potential_profit_margin, 2)),
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
                                order.update({
                                    'amount_untaxed': round(credit_amount_untaxed, 2),
                                    'amount_total': round(credit_amount_total, 2)
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
        if (temp_payment_term == False):
            temp_payment_term = '0 Days '
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.check_object_reference('vendor_offer', 'email_template_edi_vendor_offer_done', raise_on_access_error=True)[1]
            else:
                template_id = ir_model_data.check_object_reference('vendor_offer', 'email_template_edi_vendor_offer_done', raise_on_access_error=True)[1]

        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.check_object_reference('mail', 'email_compose_message_wizard_form', raise_on_access_error=True)[1]

        except ValueError:
            compose_form_id = False

        template = self.env.ref('vendor_offer.email_template_edi_vendor_offer_done', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        ctx = dict(self.env.context or {})

        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "vendor_offer.mail_notification_vendor_offer",
            'force_email': True,
            'partner_to': self.partner_id.id if not self.partner_id.vendor_email else False,
            'email_from': self.acq_user_id.partner_id.email if self.acq_user_id.partner_id.email != False else (self.sudo().create_uid.email_formatted or ''),
            'vendor_email': (self.partner_id.vendor_email or self.partner_id.email) if self.partner_id else False,
            'email_cc': self.acq_user_id.partner_id.email or ''
        })

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

        # Attaching the shipping label to email template
        if self.shipping_number:
            ship_label = self.env['ir.attachment'].search(
                [('res_model', '=', 'purchase.order'),
                 ('mimetype', '=', 'application/pdf'), ('name', 'ilike', '%' + self.name + '%'),
                 ('name', 'like', '%FedEx_Label%')], order="id desc")[0]

            if ship_label:
                template.sudo().write({'attachment_ids': [ship_label.id]})

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



