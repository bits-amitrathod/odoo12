import logging

import odoo
from odoo import models, fields,  SUPERUSER_ID,api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
from werkzeug.urls import url_encode
from datetime import datetime

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    cust_po = fields.Char("Customer PO", readonly=False)
    client_order_ref = fields.Char(string='Purchase Order#', copy=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('engine', 'Prioritization'),
        ('sent', 'Quotation Sent'),
        ('return', 'Return'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('void', 'Voided'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    preferred_method = fields.Selection(string='Preferred Invoice Delivery Method',
                                        related='partner_id.preferred_method', readonly=True)
    carrier_info = fields.Char("Carrier Info", related='partner_id.carrier_info', readonly=True)
    is_share = fields.Boolean(string='Is Shared', related='partner_id.is_share', readonly=True, store=True)
    sale_margine = fields.Selection([
        ('gifted', 'Gifted'),
        ('legacy', 'Legacy')], string='Sales Level', related='partner_id.sale_margine', readonly=True, store=True)
    carrier_acc_no = fields.Char("Carrier Account No", related='partner_id.carrier_acc_no', readonly=True)

    order_processor = fields.Many2one('res.users', string='Order Processor', index=True, tracking=True,
                              default=lambda self: self.env.user)

    gl_account = fields.Char("GL Account", store=False, compute='_get_gl_account', readonly=True)

    def _get_gl_account(self):
        for order in self:
            if order.partner_id and order.partner_id.gl_account:
                for gl_acnt in order.partner_id.gl_account:
                    if gl_acnt.name:
                        if order.gl_account:
                            order.gl_account = order.gl_account + ", " + gl_acnt.name
                        else:
                            order.gl_account = gl_acnt.name
            else:
                order.gl_account = None

    # @api.onchange('client_order_ref')
    # def update_account_invoice_purchase_order(self):
    #     self.env['account.move'].search([('invoice_origin', '=', self.name)]).update({'purchase_order': self.client_order_ref})

    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})

        return self.env.ref('sale.action_report_saleorder') \
            .with_context(discard_logo_check=True).report_action(self)

    def action_void(self):
        return self.write({'state': 'void'})

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel', 'void'):
                raise UserError(
                    'You can not delete a sent quotation or a sales order! Try to cancel or void it before.')
        return models.Model.unlink(self)

    def action_assign(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.action_assign()

    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

    def force_quotation_send(self):
        for order in self:
            email_act = order.action_quotation_send()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=order.company_id.email, force_send=False)
                order.with_context(**email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
        return True

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
            # template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
            # template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data']._xmlid_to_res_id('sale_order_cstm.mail_template_sale_confirmation_cstm', raise_if_not_found=True)
        if not template_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('sale_order_cstm.email_template_sale_custom_dub', raise_if_not_found=True)
        return template_id

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }


        if not self.order_line :
            ctx['email_from'] = None
        elif self.order_line[0] and self.order_line[0].customer_request_id and self.order_line[0].customer_request_id.\
                document_id and self.order_line[0].customer_request_id.document_id.email_from:
            ctx['email_from'] = self.order_line[0].customer_request_id.document_id.email_from
        else:
            ctx['email_from'] = None

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.add_note_in_delivery()
        if self.team_id.team_type in ('engine', 'rapid_quote'):
            user = None
            current_user = self.env['res.users'].browse(self._context.get('uid'))
            sale_order_customer = self.partner_id
            super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID)])
            user_sale_person = current_user.user_id
            user = sale_order_customer.user_id if sale_order_customer.user_id else super_user
            self.update({'user_id': user.id})

            # Send email to Salesperson and Admin when sales order accepted(Confirm)
            # upload_type = None
            # salesperson_email = None
            # if self.order_line[0].customer_request_id and self.order_line[0].customer_request_id.document_id and \
            #         self.order_line[0].customer_request_id.document_id.source:
            #     upload_type = self.order_line[0].customer_request_id.document_id.source
            # if self.user_id and self.user_id.partner_id and self.user_id.partner_id.email:
            #     salesperson_email = self.user_id.partner_id.email
            # elif self.partner_id and self.partner_id.parent_id and self.partner_id.parent_id.user_id \
            #         and self.partner_id.parent_id.user_id.partner_id and self.partner_id.parent_id.user_id.partner_id.email:
            #     salesperson_email = self.partner_id.parent_id.user_id.partner_id.email
            # if self.sale_note:
            #     note = self.sale_note
            # else:
            #     note = ""
            # self._send_sales_order_accepted_email(self.partner_id.display_name, self.name, self.state,
            #                                       salesperson_email, upload_type, note)

        return res

    def add_note_in_delivery(self):
        # Add note in pick delivery
        if self.state and self.state in 'sale':
            for pick in self.picking_ids:
                pick.note = self.sale_note

        if self.carrier_id and self.state and self.state in 'sale':
            self.env['stock.picking'].search([('sale_id', '=', self.id), ('picking_type_id', '=', 5)]).write(
                {'carrier_id': self.carrier_id.id})

        # if 'sale_note' in val or self.sale_note:
        if self.sale_note and self.team_id.team_type != 'engine':
            body = self.sale_note
            for stk_picking in self.picking_ids:
                stock_picking_val = {
                    'body': body,
                    'model': 'stock.picking',
                    'message_type': 'notification',
                    'reply_to_force_new': False,
                    'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note', raise_if_not_found=True),
                    'res_id': stk_picking.id,
                    'author_id': self.env.user.partner_id.id,
                }
                self.env['mail.message'].sudo().create(stock_picking_val)

    def _send_sales_order_accepted_email(self, customer_name, sales_order_name, sales_order_status, salespersonEmail,
                                         upload_type, note):
        today_date = datetime.today().strftime('%m/%d/%Y %H:%M:%S')
        template = self.env.ref('prioritization_engine.stockhawk_sales_order_confirm_email_response').sudo()
        local_context = {'customer_name': customer_name, 'sales_order_name': sales_order_name,
                         'salesperson_email': salespersonEmail,
                         'date': today_date, 'sales_order_status': sales_order_status, 'upload_type': upload_type,
                         'note': note}
        try:
            template.with_context(local_context).send_mail(SUPERUSER_ID, raise_exception=True)
        except Exception as exc:
            _logger.error("getting error while sending email of sales order : %r", exc)
            response = {'message': 'Unable to connect to SMTP Server'}

    def get_share_url(self, redirect=False, signup_partner=False, pid=None):
        """Override for sales order.

        If the SO is in a state where an action is required from the partner,
        return the URL with a login token. Otherwise, return the URL with a
        generic access token (no login).
        """
        self.ensure_one()
        if self.state not in ['sale', 'done']:
            auth_param = url_encode(self.partner_id.signup_get_auth_param()[self.partner_id.id])
            return self.get_portal_url(query_string='&%s' % auth_param)
        return super(SaleOrder, self)._get_share_url(redirect, signup_partner, pid)


class SaleOrderLinePrioritization(models.Model):
    _inherit = "sale.order.line"
    # customer_request_count = fields.Boolean(string='Request count', compute="_get_customer_request_count")
    customer_request_id = fields.Many2one('sps.customer.requests', string='Request')
    req_no = fields.Char(string='Requisition Number')
    req_date = fields.Date(string='Requisition Date')
    vendor = fields.Char(string='Vendor')
    item_no = fields.Char(string='Item No.')
    deliver_to_location = fields.Char(string='Deliver-to Location')
    default_code = fields.Char("SKU", store=False, readonly=True, related='product_id.product_tmpl_id.default_code')
    ex_product_desc = fields.Char("Product Description", store=False, readonly=True,
                                  related='product_id.product_tmpl_id.name')
    ex_sale_order_customer = fields.Char("Customer", store=False, readonly=True, related='order_id.partner_id.name')
    ex_sale_order_name = fields.Char("#Sale Order", store=False, readonly=True, related='order_id.name')
    # ex_sale_order_confirm_date = fields.Datetime("Date Sold", store=False, readonly=True,
    #                                              related='order_id.confirmation_date')
    ex_product_oem = fields.Char("Product OEM", store=False, readonly=True, related='product_id.product_brand_id.name')
    # manufacturer_uom = fields.Char('Manufacturer Unit of Measure',related='product_id.product_tmpl_id.manufacturer_uom.name')
    manufacturer_uom = fields.Many2one('uom.uom',
                                       'Manuf. UOM', related='product_id.product_tmpl_id.manufacturer_uom',
                                       readonly=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    '''#@api.multi
    def _get_customer_request_count(self):
        print(self)
        print(self.customer_request_id)
        print(len(self.customer_request_id))
        self.customer_request_count=len(self.customer_request_id)>0'''

    def action_show_details(self):
        multi = self.env['stock.move'].search([('sale_line_id', '=', self.id)])
        if len(multi) >= 1 and self.order_id.delivery_count == 1:
            return multi.action_show_details()
        elif self.order_id.delivery_count > 1:
            raise ValidationError(_('Picking is not possible for multiple delivery please do picking inside Delivery'))

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        # domain=[]
        if self.product_id.uom_id.id == self.product_id.manufacturer_uom.id:
            domain = {'product_uom': [('id', '=', self.product_id.uom_id.id)]}
        else:
            domain = {'product_uom': [('id', 'in', (self.product_id.uom_id.id, self.product_id.manufacturer_uom.id))]}

        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

    def get_discount(self):
        if self.order_id.team_id and self.order_id.team_id.name == 'Rapid Order':
            if not (self.product_id and self.product_uom and
                    self.order_id.partner_id and self.order_id.pricelist_id and
                    self.order_id.pricelist_id.discount_policy == 'without_discount'):
                return
        else:
            if not (self.product_id and self.product_uom and
                    self.order_id.partner_id and self.order_id.pricelist_id and
                    self.order_id.pricelist_id.discount_policy == 'without_discount' and
                    self.env.user.has_group('sale.group_discount_per_so_line')):
                return


        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                               self.product_uom_qty,
                                                                                               self.product_uom,
                                                                                               self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.order_id.pricelist_id.currency_id,
                    self.order_id.company_id or self.env.user.company_id,
                    self.order_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                return discount


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.

        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_ids and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.reserved_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if self.partner_id.on_hold:
                if picking_type.code in ("internal","outgoing"):
                    raise UserError(_('Customer is on hold. You cannot validate a transfer.'))

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product
                    elif line.qty_done == 0:
                        raise UserError(_(
                            'You cannot validate a transfer if you have not processed any quantity for %s.') % product.display_name)

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if picking_type.code == "outgoing":
            if self.state == 'done' and self.carrier_tracking_ref:
                self.env['sale.order'].search([('name', '=', self.origin)]).write({'carrier_track_ref': self.carrier_tracking_ref})

        return True


    def send_to_shipper(self):
        print("inside send to shipper")
        print(self.carrier_tracking_ref)
        self.ensure_one()
        if not self.carrier_tracking_ref:
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
        else:
            self.message_post(body="Already tracking created")


class AccountInvoice(models.Model):
    _inherit = 'account.move'
    expiration_date = fields.Date("Expiration Date")
    note = fields.Char("Customer Message")
    memo = fields.Char("Memo")
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    is_share = fields.Boolean(string='Is Shared', related='partner_id.is_share', readonly=True)
    sale_margine = fields.Selection([
        ('gifted', 'Gifted'),
        ('legacy', 'Legacy')], string='Sales Level', related='partner_id.sale_margine', readonly=True)
    preferred_method = fields.Selection(string='Preferred Invoice Delivery Method',
                                        related='partner_id.preferred_method', readonly=True)

    '''name = fields.Char(string='Purchase Order#', index=True,
                       readonly=True, states={'draft': [('readonly', False)]},
                       help='The name that will be used on account move lines')

      origin = fields.Char(string='Sale Order#',
                         help="Reference of the document that produced this invoice.",
                         readonly=True, states={'draft': [('readonly', False)]})'''

    purchase_order = fields.Char(string='Purchase Order#', store=False, compute="_setInvoicePurchaseOrder",
                                 readonly=True)
    tracking_reference = fields.Char(string=' TrackingReference', store=False,
                                     compute='_getSalesOerderPickingOutTrackingReference', readonly=True)

    def _setInvoicePurchaseOrder(self):
        for order in self:
            order.purchase_order = None
            if order.invoice_origin == order.name:
                order.purchase_order = ""
            else:
                if order.invoice_origin:
                    so =self.env['sale.order'].search([('name', '=', order.invoice_origin)])
                    if so.client_order_ref:
                        order.purchase_order=so.client_order_ref
                    else:
                        order.purchase_order = order.ref
                else:
                    order.purchase_order = order.ref

    def _getSalesOerderPickingOutTrackingReference(self):
        for order in self:
            if order.stock_move_id and order.stock_move_id.picking_id and order.stock_move_id.picking_id.carrier_tracking_ref and order.stock_move_id.picking_id.state == 'done':
                order.env.cr.execute(
                    "select carrier_tracking_ref from stock_picking WHERE id =" + order.stock_move_id.picking_id.id + " name like 'WH/OUT/%' limit 1")
                query_result = order.env.cr.dictfetchone()
                if query_result and query_result['carrier_tracking_ref']:
                    order.tracking_reference = query_result['carrier_tracking_ref']
                else:
                    order.tracking_reference = None
            else:
                order.tracking_reference = None


class SaleOrderReport(models.Model):
    _inherit = "sale.report"

    req_no = fields.Char(string='Requisition Number')