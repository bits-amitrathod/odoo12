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
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    preferred_method = fields.Selection(string='Preferred Invoice Delivery Method',
                                        related='partner_id.preferred_method', readonly=True)
    carrier_info = fields.Char("Carrier Info", related='partner_id.carrier_info', readonly=True)
    is_share = fields.Boolean(string='Is Shared', related='partner_id.is_share', readonly=True, store=True)
    sale_margine = fields.Selection([
        ('gifted', 'Gifted'),
        ('legacy', 'Legacy')], string='Sales Level', related='partner_id.sale_margine', readonly=True, store=True)
    carrier_acc_no = fields.Char("Carrier Account No", related='partner_id.carrier_acc_no', readonly=True)

    order_processor = fields.Many2one('res.users', string='Order Processor', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    gl_account = fields.Char("GL Account", store=False, compute='_get_gl_account', readonly=True)

    @api.multi
    def _get_gl_account(self):
        for order in self:
            if order.partner_id and order.partner_id.gl_account:
                for gl_acnt in order.partner_id.gl_account:
                    if gl_acnt.name:
                        if order.gl_account:
                            order.gl_account = order.gl_account + ", " + gl_acnt.name
                        else:
                            order.gl_account = gl_acnt.name

    @api.onchange('client_order_ref')
    def update_account_invoice_purchase_order(self):
        self.env['account.invoice'].search([('origin', '=', self.name)]).write({'name': self.client_order_ref})

    @api.multi
    def action_void(self):
        return self.write({'state': 'void'})

    @api.multi
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

    @api.multi
    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

    @api.multi
    def action_quotation_send(self):
        _logger.info('saleorder -> action_quotation_send()')
        """
        This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('prioritization_engine', 'email_template_sale_custom')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }

        if self.order_line[0] and self.order_line[0].customer_request_id and self.order_line[0].customer_request_id. \
                document_id and self.order_line[0].customer_request_id.document_id.email_from:
            ctx['email_from'] = self.order_line[0].customer_request_id.document_id.email_from
        else:
            ctx['email_from'] = None

        return {
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
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.team_id.team_type == 'engine':
            user = None
            current_user = self.env['res.users'].browse(self._context.get('uid'))
            sale_order_customer = self.partner_id
            super_user = self.env['res.users'].search([('id', '=', SUPERUSER_ID)])
            user_sale_person = current_user.user_id
            user = sale_order_customer.user_id if sale_order_customer.user_id else super_user
            self.update({'user_id': user.id})

            # Send email to Salesperson and Admin when sales order accepted(Confirm)
            upload_type = None
            salesperson_email = None
            if self.order_line[0].customer_request_id and self.order_line[0].customer_request_id.document_id and \
                    self.order_line[0].customer_request_id.document_id.source:
                upload_type = self.order_line[0].customer_request_id.document_id.source
            if self.user_id and self.user_id.partner_id and self.user_id.partner_id.email:
                salesperson_email = self.user_id.partner_id.email
            elif self.partner_id and self.partner_id.parent_id and self.partner_id.parent_id.user_id \
                    and self.partner_id.parent_id.user_id.partner_id and self.partner_id.parent_id.user_id.partner_id.email:
                salesperson_email = self.partner_id.parent_id.user_id.partner_id.email
            if self.sale_note:
                note = self.sale_note
            else:
                note = ""
            self._send_sales_order_accepted_email(self.partner_id.display_name, self.name, self.state,
                                                  salesperson_email, upload_type, note)

        return res

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

    @api.multi
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
    default_code = fields.Char("SKU", store=False, readonly=True, related='product_id.product_tmpl_id.default_code')
    # manufacturer_uom = fields.Char('Manufacturer Unit of Measure',related='product_id.product_tmpl_id.manufacturer_uom.name')
    manufacturer_uom = fields.Many2one('uom.uom',
                                       'Manuf. UOM', related='product_id.product_tmpl_id.manufacturer_uom',
                                       readonly=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    '''@api.multi
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

    @api.multi
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
                self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

    def get_discount(self):
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

    @api.multi
    def button_validate(self):
        _logger.info("stock :stock_picking_prioritization  button_validate called.....")
        _logger.info("stock :stock_picking_prioritization parnter hold status %r :", self.partner_id)

        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_(
                'You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))
        if self.partner_id.on_hold:
            if picking_type.code == "outgoing":
                raise UserError(_(
                    'Customer is on hold. You cannot validate a transfer.'))
        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)
                    elif line.qty_done == 0:
                        raise UserError(_(
                            'You cannot validate a transfer if you have not processed any quantity for %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {'name': _('Immediate Transfer?'), 'type': 'ir.actions.act_window', 'view_type': 'form',
                    'view_mode': 'form', 'res_model': 'stock.immediate.transfer', 'views': [(view.id, 'form')],
                    'view_id': view.id, 'target': 'new', 'res_id': wiz.id, 'context': self.env.context, }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                    'res_model': 'stock.overprocessed.transfer', 'views': [(view.id, 'form')], 'view_id': view.id,
                    'target': 'new', 'res_id': wiz.id, 'context': self.env.context, }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()

        if picking_type.code == "outgoing":
            if self.state == 'done' and self.carrier_tracking_ref:
                self.env['sale.order'].search([('name', '=', self.origin)]).write({'carrier_track_ref': self.carrier_tracking_ref})

        return

    @api.multi
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
    _inherit = 'account.invoice'
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

    @api.multi
    def _setInvoicePurchaseOrder(self):
        for order in self:
            if order.origin == order.name:
                order.purchase_order = ""
            else:
                order.purchase_order = order.name

    @api.multi
    def _getSalesOerderPickingOutTrackingReference(self):
        for order in self:
            if order.origin:
                order.env.cr.execute(
                    "select carrier_tracking_ref from stock_picking WHERE origin like '" + order.origin + "' and state like 'done' and name like 'WH/OUT/%' limit 1")
                query_result = order.env.cr.dictfetchone()
                if query_result and query_result['carrier_tracking_ref']:
                    order.tracking_reference = query_result['carrier_tracking_ref']


class SaleOrderReport(models.Model):
    _inherit = "sale.report"

    req_no = fields.Char(string='Requisition Number')