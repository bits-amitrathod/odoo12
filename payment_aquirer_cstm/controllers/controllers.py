# -*- coding: utf-8 -*-
import odoo
import hashlib
import hmac
import logging
from odoo import http
from unicodedata import normalize
from odoo.http import request
from odoo.osv import expression
from odoo.addons.portal.controllers.mail import _message_post_helper
import werkzeug
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools import ustr
from odoo.tools.translate import _
from odoo.exceptions import AccessError, MissingError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, consteq
from odoo import api, fields, models
from odoo.tools.float_utils import float_repr
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment_paypal.controllers.main import PaypalController
# from odoo.addons.website_sale_delivery.controllers.main import website_sale_delivery
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery

from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
class PaymentAquirerCstm(http.Controller):

    @http.route('/shop/payment/purchaseorderform', type='http', auth="public", website=True, csrf=False)
    def purchase_order_form_validate(self, **kwargs):
        vals = {}
        if kwargs:
            order = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
            if order.client_order_ref:
                kwargs['purchase_order'] = order.client_order_ref

            if 'purchase_order' in kwargs and kwargs['purchase_order'] != '':
                tx_id = request.session.get('__website_sale_last_tx_id')
                if tx_id:
                    transaction = request.env['payment.transaction'].sudo().browse(tx_id)
                    transaction.state = 'pending'
                    # order.state = 'sent'
                    if not order.client_order_ref:
                        if not order.x_studio_allow_duplicate_po:
                            result = request.env['sale.order'].sudo().search(
                                [('client_order_ref', '=', kwargs['purchase_order']),
                                 ('partner_id','in',order.get_chils_parent())])
                            if result:
                                result2 = request.env['sale.order'].sudo().search(
                                    [('client_order_ref', '=', kwargs['purchase_order']),
                                     ('partner_id', 'in', order.get_chils_parent()),
                                     ('x_studio_allow_duplicate_po', '=', True)
                                     ])
                                if result2:
                                    order.state = 'sent'
                                    order.client_order_ref = kwargs['purchase_order']
                                    if order.check_product_qty_before_sale():
                                        vals = {'error': " Product(s) Out Of Stack."}
                                        return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)
                                    order.action_confirm()
                                else:
                                    vals = {'error': "The PO number is already present on another Sales Order."}
                                    return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)
                            else:
                                order.state = 'sent'
                                order.client_order_ref = kwargs['purchase_order']
                                if order.check_product_qty_before_sale():
                                    vals = {'error': " Product(s) Out Of Stack."}
                                    return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)
                                order.action_confirm()
                    return request.redirect('/shop/payment/validate')
                else:
                    request.redirect('/shop')
            if 'return_url' not in kwargs:
                vals = {'error': "Please enter Purchase order"}
        # request.session.set('sale_transaction_id', request.session.get('__website_sale_last_tx_id'))
        return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)

    @http.route(['/shop/cart/updatePurchaseOrderNumber'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, purchase_order, **kw):
        order = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
        order.client_order_ref = purchase_order
        value = {'success': True}

        return value

    @http.route(['/shop/cart/expeditedShipping'], type='json', auth="public", methods=['POST'], website=True,csrf=False)
    def expedited_shipping(self, expedited_shipping):
        request.session['expedited_shipping'] = expedited_shipping

    @http.route(['/shop/get_carrier'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def get_carrier(self, delivery_carrier_code):
        order = request.website.sale_get_order()
        delivery_carriers = order._get_delivery_methods()
        delivery_carrier = delivery_carriers.filtered(lambda x: x.code == delivery_carrier_code)
        if delivery_carrier:
            return {'carrier_id': delivery_carrier.id}

    @http.route('/checkHavingCarrierWithAccountNo', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def check_having_carrier_with_account_no(self):
        Monetary = request.env['ir.qweb.field.monetary']
        order = request.website.sale_get_order()
        if not order:
            order_id = request.session.get('sale_order_id',0)
            order = request.env['sale.order'].sudo().browse(order_id)

        values = {}
        if request.env.user.partner_id.having_carrier and request.env.user.partner_id.carrier_acc_no:
            values["carrier_acc_no"] = True
        else:
            values["carrier_acc_no"] = False
            values["error_message"] = order.delivery_message
            if order.currency_id:
                currency = order.currency_id
            else:
                res_currency = request.env.user.company_id.currency_id
                if res_currency:
                    currency = res_currency
            values["status"] = order.delivery_rating_success
            values['new_amount_delivery'] = Monetary.value_to_html(order.amount_delivery, {'display_currency': currency})


        # checking for payment link
        gen_pay = False
        if order.id:
            pay_link = request.env['sale.pay.link.cust'].search([('sale_order_id', '=', order.id)])
            if pay_link and pay_link.allow_pay_gen_payment_link:
                gen_pay = True

        invoice_id = request.session.get('payment_link_invoice_id')
        if invoice_id:
            gen_pay = True

        values['gen_pay_link'] = gen_pay

        return values

class WebsiteSalesPaymentAquirerCstm(odoo.addons.website_sale.controllers.main.WebsiteSale):
    def shop_payment(self, **post):
        responce = super(WebsiteSalesPaymentAquirerCstm, self).shop_payment(**post)

        if 'expedited_shipping' not in request.session:
            request.session['expedited_shipping'] = "Ground"
        elif 'expedited_shipping' in request.session and request.session['expedited_shipping'] == "":
            request.session['expedited_shipping'] = "Ground"

        ctx = responce.qcontext

        if 'providers' not in ctx:
            ctx['showShippingNote'] = False
            ctx['expedited_shipping'] = 'expedited_shipping' in request.session and request.session[
                'expedited_shipping'] or ""
            if 'deliveries' in ctx:
                for x in ctx['deliveries']:
                    if x.delivery_type == "fixed" and x.fixed_price == 0:
                        ctx['showShippingNote'] = True
                        ctx['freeShipingLabel'] = x.code
                    break
            return responce

        # if ('order' in ctx and not ctx['order'].partner_id.allow_purchase) or ('order' not in ctx) :
        if ('order' in ctx and not ctx['order'].partner_id.allow_purchase) or ('order' not in ctx):
            if 'providers' in ctx:
                ctx['providers'] = ctx['providers'] and ctx['providers'].filtered(lambda p:p.name != 'Purchase Order')

        ctx['showShippingNote'] = False
        ctx['expedited_shipping'] = 'expedited_shipping' in request.session and request.session['expedited_shipping'] or ""
        if 'deliveries' in ctx:
            for x in ctx['deliveries']:
                if x.delivery_type == "fixed" and x.fixed_price == 0:
                    ctx['showShippingNote'] = True
                    ctx['freeShipingLabel'] = x.code
                break

        return responce

    # @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        responce = super(WebsiteSalesPaymentAquirerCstm, self).shop_payment_confirmation(**post)
        order = responce.qcontext['order']
        sale_note = ""
        if 'sales_team_message' in request.session:
            if request.session['sales_team_message']:
                sale_note = request.session['sales_team_message']
                request.session.pop('sales_team_message')

        if order.carrier_id.code == "my_shipper_account" and 'expedited_shipping' in request.session:
            if request.session['expedited_shipping']:
                if sale_note:
                    sale_note = sale_note + "\n" + "Please use customers shipper account with Method: " + \
                                request.session['expedited_shipping']
                else:
                    sale_note = "Please use customers shipper account with Method: " + \
                                request.session['expedited_shipping']
                request.session.pop('expedited_shipping')

        if sale_note:
            order.sudo().write({'sale_note': sale_note})

        # remove Product from Product Process
        product_process = request.env['product.process.list'].sudo()
        for line in order.order_line:
            # UPG_ODOO16_NOTE  line.product_id.inventory_availability "inventory_availability" field is missing on product.product model
            # if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
            if line.product_id.type == 'product' and line.product_id.show_availability:
                product_process.remove_recored_by_product_and_so(line.product_id.id, order.name)

        return responce

    @http.route()
    def payment_transaction(self, *args, **kwargs):
        order = request.website.sale_get_order()
        values = []
        values_b = []
        product_process = request.env['product.process.list'].sudo()
        # this is custom code  used to handle Same Items being sold simultaneously
        for line in order.order_line:
            # if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
            if line.product_id.type == 'product' and line.product_id.show_availability:
                cart_qty = sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped(
                    'product_uom_qty'))
                avl_qty = line.product_id.with_context(warehouse=order.warehouse_id.id).virtual_available
                if product_process.is_product_in_process(line.product_id):
                    process_qty = product_process.get_product_process_qty_by_product(line.product_id, order.name)
                    if (cart_qty + process_qty) > avl_qty:
                        values_b.append(_('You ask %(quantity)s products of SKU Name: %(sku)s but only %(available_qty)s are available',
                        sku=line.product_id.sku_code,
                        quantity=cart_qty,
                        available_qty=(avl_qty - process_qty) if(avl_qty - process_qty) > 0 else 0))
                if cart_qty > avl_qty:
                    values.append(_(
                        'You ask for %(quantity)s products but only %(available_qty)s is available',
                        quantity=cart_qty,
                        available_qty=avl_qty if avl_qty > 0 else 0
                    ))
        if values:
            raise ValidationError('. '.join(values) + '.')
        if values_b:
            raise ValidationError('. '.join(values_b) + '.')

        # add Products in process
        for line in order.order_line:
            # if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
            if line.product_id.type == 'product' and line.product_id.show_availability:
                product_process.create({
                    'product_id': line.product_id.id,
                    'so_name': order.name,
                    'process_qty': sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped(
                            'product_uom_qty')),
                    'customer_id': order.partner_id.id,
                })

        return super(WebsiteSalesPaymentAquirerCstm, self).payment_transaction(*args, **kwargs)
    @http.route('/salesTeamMessage', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def salesTeamMessage(self, sales_team_message):
        request.session['sales_team_message'] = sales_team_message


class PaymentPortalCustom(odoo.addons.payment.controllers.portal.PaymentPortal):

    def action_send_mail_after_payment_final(self, ref=None):
        template = request.env.ref('payment_aquirer_cstm.email_after_payment_done').sudo()
        if ref:
            so_name = str(ref.reference.split("-", 1)[0])
            values = {'subject': 'Payment Done - ' + so_name + ' ', 'model': None, 'res_id': False}
            email_to = 'sales@surgicalproductsolutions.com'
            sale_order = request.env['sale.order'].sudo().search([('name', '=', so_name)], limit=1)
            if sale_order:
                if sale_order.account_manager:
                    user_id_email = sale_order.account_manager.login
                elif sale_order.user_id:
                    if sale_order.user_id.name == "National Accounts" and sale_order.national_account:
                        user_id_email = sale_order.national_account.login
                    else:
                        user_id_email = sale_order.user_id.login
                elif sale_order.national_account:
                    user_id_email = sale_order.national_account.login
                else:
                    user_id_email = sale_order.user_id.login

            email_to = user_id_email

            email_cc = 'accounting@surgicalproductsolutions.com'
            email_from = "info@surgicalproductsolutions.com"

            sales_rep = sale_order.user_id.name if sale_order.user_id else None

            local_context = {'email_from': email_from, 'email_cc': email_cc, 'email_to': email_to,
                             'sale_order': so_name, 'amount': ref.amount, 'tx': ref, 'sales_rep': sales_rep,
                             'cust_name': sale_order.partner_id.name}
            try:
                sent_email_template = template.with_context(local_context).sudo().send_mail(SUPERUSER_ID,
                                                                                            raise_exception=True)
                request.env['mail.mail'].sudo().browse(sent_email_template).write(values)
            except Exception as exc:
                response = {'message': 'Unable to connect to SMTP Server'}

    def payment_pay( self, reference=None, amount=None, currency_id=None, partner_id=None, company_id=None,provider_id=None, access_token=None, **kwargs):
        res = super(PaymentPortalCustom,self).payment_pay(reference=reference,amount=amount, currency_id=currency_id, partner_id=partner_id,company_id=company_id,provider_id=provider_id,access_token=access_token,**kwargs)

        res.qcontext = res.qcontext
        # Removing the "Purchase Order" provider form provider list
        res.qcontext['providers'] = res.qcontext['providers'].filtered(lambda p: p.name != 'Purchase Order')
        # BITS custom code..below to add the sale_order and invoice ir ro session.............................
        order_id = self._cast_as_int(kwargs.get('sale_order_id',0))
        if order_id:
            request.session['sale_order_id'] = order_id
        if order_id:
            pay_link = request.env['sale.pay.link.cust'].search([('sale_order_id', '=', order_id)])
            if pay_link:
                pay_link.allow_pay_gen_payment_link = True
            else:
                request.env['sale.pay.link.cust'].create({
                    'sale_order_id': order_id,
                    'allow_pay_gen_payment_link': True
                })

        invoice_id = self._cast_as_int(kwargs.get('invoice_id'))
        if invoice_id:
            pay_link = request.env['sale.pay.link.cust'].search([('invoice_id', '=', invoice_id)])
            if pay_link:
                pay_link.allow_pay_gen_payment_link = True
            else:
                request.env['sale.pay.link.cust'].create({
                        'invoice_id': invoice_id,
                        'allow_pay_gen_payment_link': True
                    })
            request.session['payment_link_invoice_id'] = invoice_id
        return res

    # @http.route(['/website_payment/pay'], type='http', auth='public', website=True, sitemap=False)
    # def pay(self, reference='', order_id=None, amount=False, currency_id=None, provider_id=None, partner_id=False,
    #         access_token=None, **kw):
    #     """
    #     Generic payment page allowing public and logged in users to pay an arbitrary amount.
    #
    #     In the case of a public user access, we need to ensure that the payment is made anonymously - e.g. it should not be
    #     possible to pay for a specific partner simply by setting the partner_id GET param to a random id. In the case where
    #     a partner_id is set, we do an access_token check based on the payment.link.wizard model (since links for specific
    #     partners should be created from there and there only). Also noteworthy is the filtering of s2s payment methods -
    #     we don't want to create payment tokens for public users.
    #
    #     In the case of a logged in user, then we let access rights and security rules do their job.
    #     """
    #     env = request.env
    #     user = env.user.sudo()
    #     reference = normalize('NFKD', reference).encode('ascii', 'ignore').decode('utf-8')
    #     if partner_id and not access_token:
    #         raise werkzeug.exceptions.NotFound
    #     if partner_id and access_token:
    #         token_ok = request.env['payment.link.wizard'].check_token(access_token, int(partner_id), float(amount),
    #                                                                   int(currency_id))
    #         if not token_ok:
    #             raise werkzeug.exceptions.NotFound
    #
    #     invoice_id = kw.get('invoice_id')
    #
    #     # Default values
    #     values = {
    #         'amount': 0.0,
    #         'currency': user.company_id.currency_id,
    #     }
    #
    #     # Check sale order
    #     if order_id:
    #         try:
    #             order_id = int(order_id)
    #             if partner_id:
    #                 # `sudo` needed if the user is not connected.
    #                 # A public user woudn't be able to read the sale order.
    #                 # With `partner_id`, an access_token should be validated, preventing a data breach.
    #                 order = env['sale.order'].sudo().browse(order_id)
    #             else:
    #                 order = env['sale.order'].browse(order_id)
    #             values.update({
    #                 'currency': order.currency_id,
    #                 'amount': order.amount_total,
    #                 'order_id': order_id
    #             })
    #         except:
    #             order_id = None
    #
    #     if invoice_id:
    #         try:
    #             values['invoice_id'] = int(invoice_id)
    #         except ValueError:
    #             invoice_id = None
    #
    #     # Check currency
    #     if currency_id:
    #         try:
    #             currency_id = int(currency_id)
    #             values['currency'] = env['res.currency'].browse(currency_id)
    #         except:
    #             pass
    #
    #     # Check amount
    #     if amount:
    #         try:
    #             amount = float(amount)
    #             values['amount'] = amount
    #         except:
    #             pass
    #
    #     # Check reference
    #     reference_values = order_id and {'sale_order_ids': [(4, order_id)]} or {}
    #     values['reference'] = env['payment.transaction']._compute_reference(values=reference_values, prefix=reference)
    #
    #     # Check Providers
    #     providers = None
    #     if order_id and order:
    #         cid = order.company_id.id
    #     elif kw.get('company_id'):
    #         try:
    #             cid = int(kw.get('company_id'))
    #         except:
    #             cid = user.company_id.id
    #     else:
    #         cid = user.company_id.id
    #
    #     #Check partner
    #     if not user._is_public():
    #         # NOTE: this means that if the partner was set in the GET param, it gets overwritten here
    #         # This is something we want, since security rules are based on the partner - assuming the
    #         # access_token checked out at the start, this should have no impact on the payment itself
    #         # existing besides making reconciliation possibly more difficult (if the payment partner is
    #         # not the same as the invoice partner, for example)
    #         partner_id = user.partner_id.id
    #     elif partner_id:
    #         partner_id = int(partner_id)
    #
    #     values.update({
    #         'partner_id': partner_id,
    #         'bootstrap_formatting': True,
    #         'error_msg': kw.get('error_msg')
    #     })
    #
    #     provider_domain = ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', cid)]
    #     if partner_id:
    #         partner = request.env['res.partner'].browse([partner_id])
    #         provider_domain = expression.AND([
    #             provider_domain,
    #             ['|', ('country_ids', '=', False), ('country_ids', 'in', [partner.sudo().country_id.id])]
    #         ])
    #     if provider_id:
    #         providers = env['payment.provider'].browse(int(provider_id)) if provider_id else env['payment.provider'].search(provider_domain)
    #     if not providers:
    #         providers = env['payment.provider'].search(provider_domain)
    #
    #     # UPG_ODOO16_NOTE no need of below line because it is removed from odoo 16 flow
    #     # values['providers'] = self._get_acquirers_compatible_with_current_user(providers)
    #
    #     # Removing the "Purchase Order" provider form provider list
    #     values['providers'] = values['providers'].filtered(lambda p: p.name != 'Purchase Order')
    #
    #     if partner_id:
    #         values['pms'] = request.env['payment.token'].search([
    #             ('provider_id', 'in', providers.ids),
    #             ('partner_id', 'child_of', partner.commercial_partner_id.id)
    #         ])
    #     else:
    #         values['pms'] = []
    #
    #     return request.render('payment.pay', values)

    @http.route('/payment/confirmation', type='http', methods=['GET'], auth='public', website=True)
    def payment_confirm(self, tx_id, access_token, **kwargs):

        res = super(PaymentPortalCustom,self).payment_confirm(tx_id=tx_id,access_token=access_token,**kwargs)

        tx_id = self._cast_as_int(tx_id)
        if tx_id:
            tx_sudo = request.env['payment.transaction'].sudo().browse(tx_id)

        if tx_sudo and tx_sudo.reference and tx_sudo.reference.startswith("SO"):
            self.action_send_mail_after_payment_final(tx_sudo)
        return res


class PaymentProcessing(PaymentPostProcessing):

    @http.route()
    def payment_status_page(self, **kwargs):
        # Remove product from
        order_id = request.session.sale_order_id
        if order_id:
            order = request.env['sale.order'].search([('id', '=', request.session.sale_order_id)], limit=1)
            # order = request.env['sale.order'].sudo().browse(request.session.sale_order_id)
            product_process = request.env['product.process.list'].sudo()
            for line in order.order_line:
                if line.product_id.type == 'product' and line.product_id.show_availability:
                    product_process.remove_recored_by_product_and_so(line.product_id.id, order.name)
        return super(PaymentProcessing, self).display_status(**kwargs)


class PaypalController(PaypalController):
    @http.route()
    def paypal_cancel(self, **post):
        order_id = request.session.sale_order_id
        if order_id:
            order = request.env['sale.order'].sudo().browse(request.session.sale_order_id)
            # order = request.env['sale.order'].search([('id', '=', request.session.sale_order_id)], limit=1)
            product_process = request.env['product.process.list'].sudo()
            for line in order.order_line:
                if line.product_id.type == 'product' and line.product_id.show_availability:
                    product_process.remove_recored_by_product_and_so(line.product_id.id, order.name)

        return super(PaypalController, self).paypal_cancel(**post)


class website_sale_delivery_inherit(WebsiteSaleDelivery):
    def _get_shop_payment_values(self, order, **kwargs):
        values = super(WebsiteSaleDelivery, self)._get_shop_payment_values(order, **kwargs)
        has_storable_products = any(line.product_id.type in ['consu', 'product'] for line in order.order_line)
        delivery_carriers = order._get_delivery_methods()

        if has_storable_products:
            if order.carrier_id and not order.delivery_rating_success:
                order._remove_delivery_line()

            curr_partner_id = request.env.user.partner_id
            if curr_partner_id and not (curr_partner_id.having_carrier and curr_partner_id.carrier_acc_no):
                delivery_carriers = delivery_carriers.filtered(lambda x: x.code != 'my_shipper_account')

            values['deliveries'] = delivery_carriers.sudo()

        if not delivery_carriers and has_storable_products:
            values['errors'].append(
                (_('Sorry, we are unable to ship your order'),
                 _('No shipping method is available for your current order and shipping address. '
                   'Please contact us for more information.')))

        values['delivery_has_storable'] = has_storable_products
        values['delivery_action_id'] = request.env.ref('delivery.action_delivery_carrier_form').id
        return values
