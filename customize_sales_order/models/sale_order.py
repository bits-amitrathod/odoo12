# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import UserError, Warning
import logging

_logger = logging.getLogger(__name__)


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
    customer_success = fields.Many2one('res.users', store=True, readonly=True, string="Customer Success", tracking=True,  domain="['&',['active','=',True],['share','=',False]]", compute="get_customer_success")
    #allow_pay_gen_payment_link = fields.Boolean("Allow Pay", store=False, compute='get_pay_button_activate')

    # @api.onchange('client_order_ref', 'x_studio_allow_duplicate_po')
    # @api.depends('client_order_ref', 'x_studio_allow_duplicate_po')
    # def get_pay_button_activate(self):
    #     for obj in self:
    #         if 0:
    #             obj.allow_pay_gen_payment_link = False
    #         else:
    #             obj.allow_pay_gen_payment_link = True

    def _valid_field_parameter(self, field, name):
        return name == 'track_sequence' or super()._valid_field_parameter(field, name)

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        change_default=True, default=_get_default_team, tracking=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    original_team_id = fields.Many2one(
        'crm.team', 'First Sales Team',
        tracking=True, check_company=True,  # Unrequired company
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

    # Added function to get  customer success field value
    def get_customer_success(self):
        for so in self:
            so.customer_success = so.partner_id.customer_success.id

    @api.onchange('client_order_ref')
    @api.depends('client_order_ref')
    def onchange_client_order_ref(self):
        if self.client_order_ref and self.client_order_ref is not None and self.client_order_ref.strip() != '' and self.name:
            records = self.env['sale.order'].search([('client_order_ref', '=', self.client_order_ref),('partner_id', '=', self.get_chils_parent())])
            if records:
                for record in records:
                    if self.name != record.name and (self.x_studio_allow_duplicate_po is False or
                                                 record.x_studio_allow_duplicate_po is False):
                        raise Warning(("Duplicate PO number is not allowed.\n"
                                        "The PO number of this Sales Order is already present on Sales Order %s.\n "
                                        "If you want to add Duplicate PO against Sales Order, Set 'Allow Duplicate PO' "
                                        "setting ON for both Sales Order.") % record.name)
                    else:
                        _logger.info('This is unique PO')

    @api.model
    def create(self, vals):
        # add account manager
        if 'team_id' in vals:
            vals['original_team_id']=vals['team_id']
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
            if res_partner and res_partner.customer_success and res_partner.customer_success.id:
                vals['customer_success'] = res_partner.customer_success.id
            elif res_partner and res_partner.parent_id and res_partner.parent_id.customer_success and res_partner.parent_id.customer_success.id:
                vals['customer_success'] = res_partner.parent_id.customer_success.id
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
        # Add Sale note in pick,pull,out
        # Need to optimize the Code
        #TODO : We can also Move to onChange (sale_note) ,
        if self.state and self.state in 'sale' and 'sale_note' in val:
            for pick in self.picking_ids:
                pick.note = val['sale_note'] if ('sale_note' in val.keys()) else self.sale_note

        if self.carrier_id and self.state and self.state in 'sale':
            stock_pickings = self.env['stock.picking'].search([('sale_id', '=', self.id), ('picking_type_id', '=', 5)])
            for stock_picking in stock_pickings:
                if stock_picking and stock_picking.state != 'done' and stock_picking.state != 'cancel' :
                    stock_picking.write({'carrier_id': self.carrier_id.id})

        # if 'sale_note' in val or self.sale_note:
        # if self.sale_note and self.team_id.team_type != 'engine':

        # sale Note notification would be add in to Pick,Pull,Out
        if self.sale_note and 'sale_note' in val and self.team_id.team_type != 'engine':
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

        # For Follower Adding
        if self.customer_success.id:
            self.message_subscribe(partner_ids=[self.customer_success.partner_id.id])

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
        if self.partner_id and self.partner_id.customer_success and self.partner_id.customer_success.id:
            self.customer_success = self.partner_id.customer_success.id
        elif self.partner_id and self.partner_id.commercial_partner_id and self.partner_id.commercial_partner_id.customer_success \
                and self.partner_id.commercial_partner_id.customer_success.id:
            self.customer_success = self.partner_id.commercial_partner_id.customer_success.id
        # TODO: UPG_ODOO16_NOTE
        # addons/sale/models/sale_order.py line No 339-350
        # I think That Handled using Depends that's Why this is commented
        # onchange_partner_id() Removed From parent
        # super(sale_order, self).onchange_partner_id()

    def get_chils_parent(self):
        list = []
        parent_id = self.partner_id if self.partner_id.is_parent else self.partner_id.parent_id
        list = parent_id.child_ids.ids
        list.append(parent_id.id)
        return list
