# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo import _
from odoo.exceptions import UserError, Warning
import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class CustomerContract(models.Model):
    _inherit = "res.partner"

    exclude_in_stock_product_ids = fields.One2many('exclude.product.in.stock', 'partner_id')

    def _get_default_user_id(self):
        res_users = self.env['res.users'].search([('partner_id.name', '=', 'Surgical Product Solutions')])
        if res_users:
            return res_users.id

    facility_type = fields.Selection(string='Facility Type',
                                     selection=[('health_sys', 'Health System'),
                                                ('hospital', 'Hospital'),
                                                ('surgery_cen', 'Surgery Center'),
                                                ('pur_alli', 'Purchasing Alliance'),
                                                ('charity', 'Charity'),
                                                ('broker', 'Broker'),
                                                ('veterinarian', 'Veterinarian'),
                                                ('closed', 'Non-Surgery/Closed'),
                                                ('wholesale', 'Wholesale'),
                                                ('national_acc', 'National Account Target')],
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


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_note = fields.Text('Sale Notes')
    carrier_track_ref = fields.Char('Tracking Reference', store=True, readonly=True, compute='_get_carrier_tracking_ref')
    delivery_method_readonly_flag = fields.Integer('Delivery method readonly flag', default=1, compute='_get_delivery_method_readonly_flag')
    account_manager = fields.Many2one('res.users', store=True, readonly=True, string="Key Account",
                                      compute="get_account_manager", tracking=True)
    user_id = fields.Many2one('res.users', string='Business Development', index=True, tracking=True,
                              track_sequence=2, default=lambda self: self.env.user)
    national_account = fields.Many2one('res.users', store=True, readonly=True, string="National Account",
                                       compute="get_national_account", tracking=True)
    field_read_only = fields.Integer(compute="_get_user")

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        change_default=True, default=_get_default_team, tracking=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    def _get_user(self):
        if self.env.user.email in ('jtennant@surgicalproductsolutions.com', 'info@surgicalproductsolutions.com'
                                   ,'bryon@surgicalproductsolutions.com'):
            self.field_read_only = 0
        else:
            self.field_read_only = 1

    is_signature = fields.Integer(compute="_is_signature")

    @api.depends('signature')
    def _is_signature(self):
        clean = re.compile('<.*?>')
        if self.order_processor.signature:
            clean_text = re.sub(clean, '', self.order_processor.signature)
        else:
            clean_text = ''
        if len(clean_text.strip()) > 0:
            self.is_signature = 1
        else:
            self.is_signature = 0

    def get_account_manager(self):
        for so in self:
            so.account_manager = so.partner_id.account_manager_cust.id

    def get_national_account(self):
        for so in self:
            so.national_account = so.partner_id.national_account_rep.id

    @api.onchange('client_order_ref', 'x_studio_allow_duplicate_po')
    @api.depends('client_order_ref', 'x_studio_allow_duplicate_po')
    def onchange_client_order_ref(self):
        if self.client_order_ref and self.client_order_ref is not None and self.client_order_ref.strip() != '' and self.name:
            records = self.env['sale.order'].search([('client_order_ref', '=', self.client_order_ref),('partner_id', '=', self.get_chils_parent())])
            if records:
                for record in records:
                    if self.name != record.name and (self.x_studio_allow_duplicate_po is False or
                                                 record.x_studio_allow_duplicate_po is False):
                        raise Warning(_("Duplicate PO number is not allowed.\n"
                                        "The PO number of this Sales Order is already present on Sales Order %s.\n "
                                        "If you want to add Duplicate PO against Sales Order, Set 'Allow Duplicate PO' "
                                        "setting ON for both Sales Order.") % record.name)
                    else:
                        _logger.info('This is unique PO')

    @api.model
    def create(self, vals):
        # add account manager
        if 'partner_id' in vals and vals['partner_id'] is not None:
            res_partner = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
            if res_partner and res_partner.user_id and res_partner.user_id.id:
                vals['user_id'] = res_partner.user_id.id
            elif res_partner and res_partner.parent_id and res_partner.parent_id.user_id and res_partner.parent_id.user_id.id:
                vals['user_id'] = res_partner.parent_id.user_id.id
            if res_partner and res_partner.account_manager_cust and res_partner.account_manager_cust.id:
                vals['account_manager'] = res_partner.account_manager_cust.id
            elif res_partner and res_partner.parent_id and res_partner.parent_id.account_manager_cust and res_partner.parent_id.account_manager_cust.id:
                vals['account_manager'] = res_partner.parent_id.account_manager_cust.id
            if res_partner and res_partner.national_account_rep and res_partner.national_account_rep.id:
                vals['national_account'] = res_partner.national_account_rep.id
            elif res_partner and res_partner.parent_id and res_partner.parent_id.national_account_rep and res_partner.parent_id.national_account_rep.id:
                vals['national_account'] = res_partner.parent_id.national_account_rep.id
        return super(sale_order, self).create(vals)

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            stockhawk_additional_discount = 5  # In Percent(5%)

            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def write(self, val):
        super(sale_order, self).write(val)
        # Add note in pick delivery
        if self.state and self.state in 'sale':
            for pick in self.picking_ids:
                pick.note = val['sale_note'] if ('sale_note' in val.keys()) else self.sale_note

        if self.carrier_id and self.state and self.state in 'sale':
            stock_pickings = self.env['stock.picking'].search([('sale_id', '=', self.id), ('picking_type_id', '=', 5)])
            for stock_picking in stock_pickings:
                if stock_picking and stock_picking.state != 'done' and stock_picking.state != 'cancel' :
                    stock_picking.write({'carrier_id': self.carrier_id.id})

        # if 'sale_note' in val or self.sale_note:
        if self.sale_note and self.team_id.team_type != 'engine':
            body = self.sale_note
            for stk_picking in self.picking_ids:
                stock_picking_val = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'no_auto_thread': False,
                    'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                    'res_id': stk_picking.id,
                    'author_id': self.env.user.partner_id.id,
                }
                self.env['mail.message'].sudo().create(stock_picking_val)

    def _get_carrier_tracking_ref(self):
        for so in self:
            stock_picking = self.env['stock.picking'].search([('origin', '=', so.name), ('picking_type_id', '=', 5),
                                                              ('state', 'in', ['done', 'waiting', 'assigned'])])
            for sp in stock_picking:
                if sp.carrier_tracking_ref:
                    so.carrier_track_ref = sp.carrier_tracking_ref
                    break
            break

    def _get_delivery_method_readonly_flag(self):
        delivery_method_flag = 1
        for sale_ordr in self:
            if sale_ordr.state in ('draft', 'sent', 'sale'):
                if sale_ordr.state == 'sale':
                    stock_pickings = self.env['stock.picking'].search(
                        [('sale_id', '=', sale_ordr.id), ('picking_type_id', '=', 1)])
                    for stock_picking in stock_pickings:
                        if stock_picking.state in ('assigned', 'draft', 'waiting', 'confirmed'):
                            delivery_method_flag = 1
                        else:
                            delivery_method_flag = 0
                else:
                    delivery_method_flag = 1
        sale_ordr.delivery_method_readonly_flag = delivery_method_flag
        return delivery_method_flag

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if self.state in ('draft', 'sent', 'sale'):
            # self.delivery_price = 0.0
            self.delivery_rating_success = False
            self.delivery_message = False

    def set_delivery_line(self, carrier, amount):
        # Remove delivery products from the sales order
        self._remove_delivery_line()

        for order in self:
            order.carrier_id = carrier.id
            order._create_delivery_line(carrier, amount)
            if order.carrier_id and order.state in 'sale':
                self.env['stock.picking'].search([('sale_id', '=', order.id), ('picking_type_id', '=', 5)]).write({'carrier_id':order.carrier_id.id})
        return True

    def get_delivery_price(self):
        for order in self.filtered(lambda o: o.state in ('draft', 'sent', 'sale') and len(o.order_line) > 0):
            # We do not want to recompute the shipping price of an already validated/done SO
            # or on an SO that has no lines yet
            order.delivery_rating_success = False
            res = order.carrier_id.rate_shipment(order)
            if res['success']:
                order.delivery_rating_success = True
                order.delivery_price = res['price']
                order.delivery_message = res['warning_message']
            else:
                order.delivery_rating_success = False
                order.delivery_price = 0.0
                order.delivery_message = res['error_message']

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.account_manager_cust and self.partner_id.account_manager_cust.id:
            self.account_manager = self.partner_id.account_manager_cust.id
        elif self.partner_id and self.partner_id.commercial_partner_id and self.partner_id.commercial_partner_id.account_manager_cust \
                and self.partner_id.commercial_partner_id.account_manager_cust.id:
            self.account_manager = self.partner_id.commercial_partner_id.account_manager_cust.id
        if self.partner_id and self.partner_id.national_account_rep and self.partner_id.national_account_rep.id:
            self.national_account = self.partner_id.national_account_rep.id
        elif self.partner_id and self.partner_id.commercial_partner_id and self.partner_id.commercial_partner_id.national_account_rep \
                and self.partner_id.commercial_partner_id.national_account_rep.id:
            self.national_account = self.partner_id.commercial_partner_id.national_account_rep.id
        super(sale_order, self).onchange_partner_id()

    def get_chils_parent(self):
        list = []
        parent_id = self.partner_id if self.partner_id.is_parent else self.partner_id.parent_id
        list = parent_id.child_ids.ids
        list.append(parent_id.id)
        return list


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    note_readonly_flag = fields.Integer('Delivery Note readonly flag', default=0)
    # note = fields.Text('Notes', compute='_get_note')
    #
    # def _get_note(self):
    #     for stock_picking in self:
    #         sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
    #         stock_picking.note = sale_order.sale_note

    def button_validate(self):
        action = super(StockPicking, self).button_validate()

        # Note Section code
        if self.sale_id:
            if self.picking_type_id.name == "Pick" and self.state == "done":
                self.note_readonly_flag = 1
                self.add_note_in_log_section()
                for picking_id in self.sale_id.picking_ids:
                    if picking_id.state != 'cancel' and (picking_id.picking_type_id.name == 'Pull' and picking_id.state == 'assigned'):
                        picking_id.note = self.note
            elif self.picking_type_id.name == "Pull" and self.state == "done":
                self.note_readonly_flag = 1
                self.add_note_in_log_section()
                for picking_id in self.sale_id.picking_ids:
                    if picking_id.state != 'cancel' and (picking_id.picking_type_id.name == 'Delivery Orders' and picking_id.state == 'assigned'):
                        picking_id.note = self.note
            elif self.picking_type_id.name == "Delivery Orders" and self.state == "done":
                self.note_readonly_flag = 1
                self.add_note_in_log_section()

        if self.picking_type_id.code == "outgoing":
            if self.state == 'done' and self.carrier_id and self.carrier_tracking_ref:
                sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
                sale_order.carrier_track_ref = self.carrier_tracking_ref
                if sale_order.carrier_id.id is False:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.amount_delivery = self.carrier_price
                    sale_order.set_delivery_line(self.carrier_id, self.carrier_price)
                if sale_order.carrier_id.id != self.carrier_id.id:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.amount_delivery = self.carrier_price
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
                else:
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
        return action

    def cancel_shipment(self):
        self.carrier_id.cancel_shipment(self)
        msg = "Shipment %s cancelled" % self.carrier_tracking_ref
        self.message_post(body=msg)
        self.carrier_tracking_ref = False
        sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
        sale_order.carrier_track_ref = False

    def update_sale_order_line(self, sale_order, carrier, price_unit):
        sale_order_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id), ('is_delivery', '=', True)])

        if len(sale_order_line) == 1:
            if sale_order.partner_id:
                # set delivery detail in the customer language
                carrier = carrier.with_context(lang=sale_order.partner_id.lang)

            # Apply fiscal position
            taxes = carrier.product_id.taxes_id.filtered(lambda t: t.company_id.id == sale_order.company_id.id)
            taxes_ids = taxes.ids
            if sale_order.partner_id and sale_order.fiscal_position_id:
                taxes_ids = sale_order.fiscal_position_id.map_tax(taxes, carrier.product_id, sale_order.partner_id).ids

            carrier_with_partner_lang = carrier.with_context(lang=sale_order.partner_id.lang)

            if carrier_with_partner_lang.product_id.description_sale:
                so_description = '%s: %s' % (carrier_with_partner_lang.name,
                                             carrier_with_partner_lang.product_id.description_sale)
            else:
                so_description = carrier_with_partner_lang.name

            # Update the sales order line
            sale_order_line.write({'name': so_description, 'price_unit':price_unit,'product_uom': carrier.product_id.uom_id.id, 'product_id': carrier.product_id.id, 'tax_id': [(6, 0, taxes_ids)]})

    def add_note_in_log_section(self):
        if self.note:
            body = self.note
            for stk_picking in self.sale_id.picking_ids:
                stock_picking_val = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'no_auto_thread': False,
                    'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                    'res_id': stk_picking.id,
                    'author_id': self.env.user.partner_id.id,
                }
                self.env['mail.message'].sudo().create(stock_picking_val)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self.with_context(default_customer=False)).create(vals_list)
        for user in users:
            user.partner_id.write({'customer_rank': 1})
            account_payment_term = self.env['account.payment.term'].search([('name', '=', 'Net 30'), ('active', '=', True)])
            if account_payment_term:
                user.partner_id.write({'property_payment_term_id': account_payment_term.id,
                                       'property_supplier_payment_term_id': account_payment_term.id})
        return users
