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
from odoo.exceptions import AccessError, MissingError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, consteq, ustr
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_repr

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
                                    order.action_confirm()
                                else:
                                    vals = {'error': "The PO number is already present on another Sales Order."}
                                    return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)
                            else:
                                order.state = 'sent'
                                order.client_order_ref = kwargs['purchase_order']
                                order.action_confirm()
                    return request.redirect('/shop/payment/validate')
                else:
                    request.redirect('/shop')
            if 'return_url' not in kwargs:
                vals = {'error': "Please enter Purchase order"}
        # request.session.set('sale_transaction_id', request.session.get('__website_sale_last_tx_id'))
        return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)

    @http.route(['/shop/cart/updatePurchaseOrderNumber'], type='json', auth="public", methods=['POST'], website=True,
                csrf=False)
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
        delivery_carrier = request.env['delivery.carrier'].sudo().search([('code', '=', delivery_carrier_code)])
        if delivery_carrier:
            return {'carrier_id': delivery_carrier.id}

    @http.route('/checkHavingCarrierWithAccountNo', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def check_having_carrier_with_account_no(self):
        Monetary = request.env['ir.qweb.field.monetary']
        order = request.website.sale_get_order()
        if request.env.user.partner_id.having_carrier and request.env.user.partner_id.carrier_acc_no:
            return {'carrier_acc_no': True}
        else:
            if order.currency_id:
                currency = order.currency_id
            else:
                res_currency = request.env.user.company_id.currency_id
                if res_currency:
                    currency = res_currency
            # return {
            #     'carrier_acc_no': False,
            #     'status': order.delivery_rating_success,
            #     'error_message': order.delivery_message,
            #     'is_free_delivery': not bool(order.amount_delivery),
            #     'new_amount_delivery': Monetary.value_to_html(order.amount_delivery, {'display_currency': currency}),
            #     'new_amount_untaxed': Monetary.value_to_html(order.amount_untaxed, {'display_currency': currency}),
            #     'new_amount_tax': Monetary.value_to_html(order.amount_tax, {'display_currency': currency}),
            #     'new_amount_total': Monetary.value_to_html(order.amount_total, {'display_currency': currency}),
            # }

            gen_pay = False
            if order.id:
                pay_link = request.env['sale.pay.link.cust'].search([('sale_order_id', '=', order.id)])
                if pay_link and pay_link.allow_pay_gen_payment_link:
                    gen_pay = True

            invoice_id = request.session.get('payment_link_invoice_id')
            if invoice_id:
                gen_pay = True

            return {'carrier_acc_no': False, 'error_message': order.delivery_message, 'new_amount_delivery': Monetary.value_to_html(order.amount_delivery, {'display_currency': currency}), 'status': order.delivery_rating_success, 'gen_pay_link': gen_pay}

    # def _format_amount(self, amount, currency):
    #     fmt = "%.{0}f".format(currency.decimal_places)
    #     lang = request.env['res.lang']._lang_get(request.env.context.get('lang') or 'en_US')
    #     return lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
    #         .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')


class WebsiteSalesPaymentAquirerCstm(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        responce = super(WebsiteSalesPaymentAquirerCstm, self).payment(**post)

        if 'expedited_shipping' not in request.session:
            request.session['expedited_shipping'] = "Ground"
        elif 'expedited_shipping' in request.session and request.session['expedited_shipping'] == "":
            request.session['expedited_shipping'] = "Ground"

        ctx = responce.qcontext

        if 'acquirers' not in ctx:
            ctx['showShippingNote'] = False
            ctx['expedited_shipping'] = 'expedited_shipping' in request.session and request.session[
                'expedited_shipping'] or ""
            for x in ctx['deliveries']:
                if x.delivery_type == "fixed" and x.fixed_price == 0:
                    ctx['showShippingNote'] = True
                    ctx['freeShipingLabel'] = x.code
                break
            return responce

        if 'order' in ctx:
            if not ctx['order'].partner_id.allow_purchase:
                for x in ctx['acquirers']:
                    if x.name == 'Purchase Order':
                        ctx['acquirers'].remove(x)
        else:
            if 'acquirers' in ctx:
                for x in ctx['acquirers']:
                    if x.name == 'Purchase Order':
                        ctx['acquirers'].remove(x)

        ctx['showShippingNote'] = False
        ctx['expedited_shipping'] = 'expedited_shipping' in request.session and request.session['expedited_shipping'] or ""
        for x in ctx['deliveries']:
            if x.delivery_type == "fixed" and x.fixed_price == 0:
                ctx['showShippingNote'] = True
                ctx['freeShipingLabel'] = x.code
            break

        return responce

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        responce = super(WebsiteSalesPaymentAquirerCstm, self).payment_confirmation(**post)
        order = responce.qcontext['order']
        sale_note = ""
        if 'sales_team_message' in request.session:
            if request.session['sales_team_message']:
                sale_note = request.session['sales_team_message']
                request.session.pop('sales_team_message')
                # order_sudo = order.sudo()
                # body = _(sale_note)
                # _message_post_helper(res_model='sale.order', res_id=order_sudo.id, message=body,
                #                      message_type='notification', subtype="mail.mt_note",
                #                      **({'token': order.access_token} if order.access_token else {}))

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

        return responce



    @http.route('/salesTeamMessage', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def salesTeamMessage(self, sales_team_message):
        request.session['sales_team_message'] = sales_team_message


class WebsitePaymentCustom(odoo.addons.payment.controllers.portal.WebsitePayment):

    def action_send_mail_after_payment(self, order_id=None):
        template = request.env.ref('payment_aquirer_cstm.email_after_payment_done').sudo()
        order = request.env['sale.order'].search([('id', '=', order_id)], limit=1)

        if order:
            values = {'subject': 'Payment In Process - ' + order.name + ' ', 'model': None, 'res_id': False}
            email_to = 'sales@surgicalproductsolutions.com'
            email_cc = 'accounting@surgicalproductsolutions.com'
            email_from = "info@surgicalproductsolutions.com"

            local_context = {'email_from': email_from, 'email_cc': email_cc, 'email_to': email_to, 'sale_order': order.name}
            try:
                sent_email_template = template.with_context(local_context).sudo().send_mail(SUPERUSER_ID,
                                                                                            raise_exception=True)
                request.env['mail.mail'].sudo().browse(sent_email_template).write(values)
            except Exception as exc:
                response = {'message': 'Unable to connect to SMTP Server'}

    @http.route(['/website_payment/pay'], type='http', auth='public', website=True, sitemap=False)
    def pay(self, reference='', order_id=None, amount=False, currency_id=None, acquirer_id=None, partner_id=False,
            access_token=None, **kw):
        """
        Generic payment page allowing public and logged in users to pay an arbitrary amount.

        In the case of a public user access, we need to ensure that the payment is made anonymously - e.g. it should not be
        possible to pay for a specific partner simply by setting the partner_id GET param to a random id. In the case where
        a partner_id is set, we do an access_token check based on the payment.link.wizard model (since links for specific
        partners should be created from there and there only). Also noteworthy is the filtering of s2s payment methods -
        we don't want to create payment tokens for public users.

        In the case of a logged in user, then we let access rights and security rules do their job.
        """
        env = request.env
        user = env.user.sudo()
        reference = normalize('NFKD', reference).encode('ascii', 'ignore').decode('utf-8')
        if partner_id and not access_token:
            raise werkzeug.exceptions.NotFound
        if partner_id and access_token:
            token_ok = request.env['payment.link.wizard'].check_token(access_token, int(partner_id), float(amount),
                                                                      int(currency_id))
            if not token_ok:
                raise werkzeug.exceptions.NotFound

        invoice_id = kw.get('invoice_id')

        # Default values
        values = {
            'amount': 0.0,
            'currency': user.company_id.currency_id,
        }

        # Check sale order
        if order_id:
            try:
                order_id = int(order_id)
                if partner_id:
                    # `sudo` needed if the user is not connected.
                    # A public user woudn't be able to read the sale order.
                    # With `partner_id`, an access_token should be validated, preventing a data breach.
                    order = env['sale.order'].sudo().browse(order_id)
                else:
                    order = env['sale.order'].browse(order_id)
                values.update({
                    'currency': order.currency_id,
                    'amount': order.amount_total,
                    'order_id': order_id
                })
            except:
                order_id = None

        if invoice_id:
            try:
                values['invoice_id'] = int(invoice_id)
            except ValueError:
                invoice_id = None

        # Check currency
        if currency_id:
            try:
                currency_id = int(currency_id)
                values['currency'] = env['res.currency'].browse(currency_id)
            except:
                pass

        # Check amount
        if amount:
            try:
                amount = float(amount)
                values['amount'] = amount
            except:
                pass

        # Check reference
        reference_values = order_id and {'sale_order_ids': [(4, order_id)]} or {}
        values['reference'] = env['payment.transaction']._compute_reference(values=reference_values, prefix=reference)

        # Check acquirer
        acquirers = None
        if order_id and order:
            cid = order.company_id.id
        elif kw.get('company_id'):
            try:
                cid = int(kw.get('company_id'))
            except:
                cid = user.company_id.id
        else:
            cid = user.company_id.id

        #Check partner
        if not user._is_public():
            # NOTE: this means that if the partner was set in the GET param, it gets overwritten here
            # This is something we want, since security rules are based on the partner - assuming the
            # access_token checked out at the start, this should have no impact on the payment itself
            # existing besides making reconciliation possibly more difficult (if the payment partner is
            # not the same as the invoice partner, for example)
            partner_id = user.partner_id.id
        elif partner_id:
            partner_id = int(partner_id)

        #if user._is_public():
        if order_id:
            request.session['sale_order_id'] = order_id
        if order_id and order:
            pay_link = request.env['sale.pay.link.cust'].search([('sale_order_id', '=', order_id)])
            if pay_link:
                pay_link.allow_pay_gen_payment_link = True
            else:
                log_id = request.env['sale.pay.link.cust'].create({
                    'sale_order_id': order_id,
                    'allow_pay_gen_payment_link': True
                })
            partner_id = int(partner_id)

        if invoice_id:
            pay_link = request.env['sale.pay.link.cust'].search([('invoice_id', '=', invoice_id)])
            if pay_link:
                pay_link.allow_pay_gen_payment_link = True
                request.session['payment_link_invoice_id'] = invoice_id
            else:
                log_id = request.env['sale.pay.link.cust'].create({
                        'invoice_id': invoice_id,
                        'allow_pay_gen_payment_link': True
                    })
                request.session['payment_link_invoice_id'] = invoice_id
                partner_id = int(partner_id)

        values.update({
            'partner_id': partner_id,
            'bootstrap_formatting': True,
            'error_msg': kw.get('error_msg')
        })

        acquirer_domain = ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', cid)]
        if partner_id:
            partner = request.env['res.partner'].browse([partner_id])
            acquirer_domain = expression.AND([
                acquirer_domain,
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [partner.sudo().country_id.id])]
            ])
        if acquirer_id:
            acquirers = env['payment.acquirer'].browse(int(acquirer_id))
        if order_id:
            acquirers = env['payment.acquirer'].search(acquirer_domain)
        if not acquirers:
            acquirers = env['payment.acquirer'].search(acquirer_domain)

        values['acquirers'] = self._get_acquirers_compatible_with_current_user(acquirers)
        for item in values['acquirers']:
            if item.display_name == 'Purchase Order':
                values['acquirers'].remove(item)
        if partner_id:
            values['pms'] = request.env['payment.token'].search([
                ('acquirer_id', 'in', acquirers.ids),
                ('partner_id', 'child_of', partner.commercial_partner_id.id)
            ])
        else:
            values['pms'] = []

        self.action_send_mail_after_payment(order_id)
        return request.render('payment.pay', values)

    @http.route(['/website_payment/token/<string:reference>/<string:amount>/<string:currency_id>',
                 '/website_payment/token/v2/<string:amount>/<string:currency_id>/<path:reference>',
                 '/website_payment/token/v2/<string:amount>/<string:currency_id>/<path:reference>/<int:partner_id>'],
                type='http', auth='public', website=True)
    def payment_token(self, pm_id, reference, amount, currency_id, partner_id=False, return_url=None, **kwargs):
        token = request.env['payment.token'].browse(int(pm_id))
        order_id = kwargs.get('order_id')
        invoice_id = kwargs.get('invoice_id')

        if not token:
            return request.redirect('/website_payment/pay?error_msg=%s' % _('Cannot setup the payment.'))

        values = {
            'acquirer_id': token.acquirer_id.id,
            'reference': reference,
            'amount': float(amount),
            'currency_id': int(currency_id),
            'partner_id': int(partner_id),
            'payment_token_id': int(pm_id),
            'type': 'server2server',
            'return_url': return_url,
        }

        if order_id:
            values['sale_order_ids'] = [(6, 0, [int(order_id)])]
        if invoice_id:
            values['invoice_ids'] = [(6, 0, [int(invoice_id)])]

        tx = request.env['payment.transaction'].sudo().with_context(lang=None).create(values)
        odoo.addons.payment.controllers.portal.PaymentProcessing.add_payment_transaction(tx)

        try:
            tx.s2s_do_transaction()
            secret = request.env['ir.config_parameter'].sudo().get_param('database.secret')
            token_str = '%s%s%s' % (
            tx.id, tx.reference, float_repr(tx.amount, precision_digits=tx.currency_id.decimal_places))
            token = hmac.new(secret.encode('utf-8'), token_str.encode('utf-8'), hashlib.sha256).hexdigest()
            tx.return_url = return_url or '/website_payment/confirm?tx_id=%d&access_token=%s' % (tx.id, token)

        except Exception as e:
            _logger.exception(e)
        return request.redirect('/payment/process')


