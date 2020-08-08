# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import _
from odoo.exceptions import UserError


class CustomerContract(models.Model):
    _inherit = "res.partner"

    def _get_default_user_id(self):
        res_users = self.env['res.users'].search([('partner_id.name', '=', 'Surgical Product Solutions')])
        if res_users:
            return res_users.id

    account_manager_cust = fields.Many2one('res.users', string="Key Account(KA)", domain="[('active', '=', True)"
                                                                                         ",('share','=',False)]")
    user_id = fields.Many2one('res.users', string='Business Development(BD)', help='The internal user in charge of this contact.',
                              default=_get_default_user_id)

    national_account_rep = fields.Many2one('res.users', string="National Account Rep.(NA)",
                                           domain="[('active', '=', True), ('share','=',False)]")


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_note = fields.Text('Sale Notes')
    carrier_track_ref = fields.Char('Tracking Reference', store=True, readonly=True, compute='_get_carrier_tracking_ref')
    delivery_method_readonly_flag = fields.Integer('Delivery method readonly flag', default=1, compute='_get_delivery_method_readonly_flag')
    account_manager = fields.Many2one('res.users', store=True, readonly=True, string="Key Account", compute="get_account_manager")
    user_id = fields.Many2one('res.users', string='Business Development', index=True, track_visibility='onchange',
                              track_sequence=2, default=lambda self: self.env.user)
    national_account = fields.Many2one('res.users', store=True, readonly=True, string="National Account",
                                       compute="get_national_account")

    @api.one
    def get_account_manager(self):
        for so in self:
            so.account_manager = so.partner_id.account_manager_cust.id

    @api.one
    def get_national_account(self):
        for so in self:
            so.national_account = so.partner_id.national_account_rep.id

    @api.model
    def create(self, vals):
        # add account manager
        if 'partner_id' in vals and vals['partner_id'] is not None:
            res_partner = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
            if res_partner and res_partner.account_manager_cust and res_partner.account_manager_cust.id:
                vals['account_manager'] = res_partner.account_manager_cust.id
            if res_partner and res_partner.national_account_rep and res_partner.national_account_rep.id:
                vals['national_account'] = res_partner.national_account_rep.id
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
        # Add note in pick delivery
        if self.sale_note and self.state in 'sale':
            for pick in self.picking_ids:
                if pick.picking_type_id.name == 'Pick':
                    pick.note = self.sale_note

        if self.carrier_id and self.state in 'sale':
            self.env['stock.picking'].search([('sale_id', '=', self.id), ('picking_type_id', '=', 5)]).write({'carrier_id':self.carrier_id.id})

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

        # add account manager
        if self.partner_id and self.partner_id.account_manager_cust and self.partner_id.account_manager_cust.id:
            val['account_manager'] = self.partner_id.account_manager_cust.id
        if self.partner_id and self.partner_id.national_account_rep and self.partner_id.national_account_rep.id:
            val['account_manager'] = self.partner_id.national_account_rep.id
        return super(sale_order, self).write(val)

    @api.one
    def _get_carrier_tracking_ref(self):
        for so in self:
            stock_picking = self.env['stock.picking'].search([('origin', '=', so.name), ('picking_type_id', '=', 5),
                                                              ('state', 'in', ['done', 'waiting', 'assigned'])])
            for sp in stock_picking:
                if sp.carrier_tracking_ref:
                    so.carrier_track_ref = sp.carrier_tracking_ref
                    break
            break

    @api.one
    def _get_delivery_method_readonly_flag(self):
        for sale_ordr in self:
            if sale_ordr.state in ('draft', 'sent'):
                sale_ordr.delivery_method_readonly_flag = 1
            elif sale_ordr.state == 'sale':
                stock_pickings = self.env['stock.picking'].search([('sale_id', '=', sale_ordr.id),('picking_type_id', '=', 1)])
                for stock_picking in stock_pickings:
                    if stock_picking.state == 'assigned':
                        sale_ordr.delivery_method_readonly_flag = 1

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if self.state in ('draft', 'sent', 'sale'):
            self.delivery_price = 0.0
            self.delivery_rating_success = False
            self.delivery_message = False

    @api.multi
    def set_delivery_line(self):
        # Remove delivery products from the sales order
        self._remove_delivery_line()

        for order in self:
            if order.state not in ('draft', 'sent', 'sale'):
                raise UserError(_('You can add delivery price only on unconfirmed quotations.'))
            elif not order.carrier_id:
                raise UserError(_('No carrier set for this order.'))
            elif not order.delivery_rating_success:
                raise UserError(_('Please use "Check price" in order to compute a shipping price for this quotation.'))
            else:
                price_unit = order.carrier_id.rate_shipment(order)['price']
                # TODO check whether it is safe to use delivery_price here
                order._create_delivery_line(order.carrier_id, price_unit)
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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    note_readonly_flag = fields.Integer('Delivery Note readonly flag', default=0)
    # note = fields.Text('Notes', compute='_get_note')
    #
    # def _get_note(self):
    #     for stock_picking in self:
    #         sale_order = self.env['sale.order'].search([('name', '=', stock_picking.origin)])
    #         stock_picking.note = sale_order.sale_note

    @api.multi
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
                    sale_order.delivery_price = self.carrier_price
                if sale_order.carrier_id.id != self.carrier_id.id:
                    sale_order.carrier_id = self.carrier_id.id
                    sale_order.delivery_price = self.carrier_price
                    sale_order.amount_delivery = self.carrier_price
                    self.update_sale_order_line(sale_order, self.carrier_id, self.carrier_price)
        return action

    @api.one
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