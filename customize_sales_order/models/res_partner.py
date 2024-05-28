# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class CustomerContract(models.Model):
    _inherit = "res.partner"

    exclude_in_stock_product_ids = fields.One2many('exclude.product.in.stock', 'partner_id')
    customer_success = fields.Many2one('res.users', store=True, readonly=True, string="Customer Success", racking=True)
    def _get_default_user_id(self):
        res_users = self.env['res.users'].search([('partner_id.name', '=', 'Surgical Product Solutions')])
        if res_users:
            return res_users.id

    facility_tpcd = fields.Selection(string='Facility Type',
                                     selection=[('health_sys', 'Health System'),
                                                ('hospital', 'Hospital'),
                                                ('surgery_cen', 'Surgery Center'),
                                                ('pur_alli', 'Purchasing Alliance'),
                                                ('charity', 'Charity'),
                                                ('broker', 'Broker'),
                                                ('veterinarian', 'Veterinarian'),
                                                ('closed', 'Non-Surgery/Closed'),
                                                ('wholesale', 'Wholesale'),
                                                ('national_acc', 'National Account Target'),
                                                ('other', 'Other'),
                                                ('lab/_research_center', 'Lab/ Research Center'),
                                                ('closed1', 'Closed'),
                                                ('no_surgery', 'No Surgery'),
                                                ('plastic_center', 'Plastic Center'),
                                                ('eye_center', 'Eye Center'),
                                                ],
                                     tracking=True)

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type',tracking=True)

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'

    account_manager_cust = fields.Many2one('res.users', string="Key Account(KA)", domain="[('active', '=', True)"
                                                                                         ",('share','=',False)]", tracking=True)
    user_id = fields.Many2one('res.users', string='Business Development(BD)', help='The internal user in charge of this contact.',
                              default=_get_default_user_id, tracking=True)

    national_account_rep = fields.Many2one('res.users', string="National Account Rep.(NA)",
                                           domain="[('active', '=', True), ('share','=',False)]", tracking=True)

    order_quota = fields.Float(string="Order Quota", help="Number of transactions", tracking=True,
                               digits=dp.get_precision('Product Price'))

    revenue_quota = fields.Monetary(string="Revenue Quota", help="Amount", tracking=True)

    reinstated_date = fields.Datetime(string='Reinstated Date', tracking=True)

    charity = fields.Boolean(string='Is a Charity?', tracking=True)

    display_reinstated_date_flag = fields.Integer(default=0, compute="_display_reinstated_date_flag")

    todays_notification = fields.Boolean(string='Todays Notification', default=False)

    @api.depends('category_id')
    def _display_reinstated_date_flag(self):
        reinstated_date_flag = False
        for record in self:
            if record and record.category_id:
                for category_id in record.category_id:
                    if category_id.name.strip().upper() == 'REINSTATED':
                        reinstated_date_flag = True
        if reinstated_date_flag:
            self.display_reinstated_date_flag = 1
        else:
            self.display_reinstated_date_flag = 0

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        self.customer_rank = 1
        account_payment_term = self.env['account.payment.term'].search([('name', '=', 'Net 30'), ('active', '=', True)])
        if account_payment_term:
            self.property_payment_term_id = account_payment_term.id
            self.property_supplier_payment_term_id = account_payment_term.id
        return super(CustomerContract, self).onchange_parent_id()