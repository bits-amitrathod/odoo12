# -*- coding: utf-8 -*-
import odoo
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.exceptions import AccessError, MissingError
from odoo.tools import consteq
from odoo import api, fields, models, _


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
                                 ('partner_id','=',order.partner_id.id)])
                            if result:
                                result2 = request.env['sale.order'].sudo().search(
                                    [('client_order_ref', '=', kwargs['purchase_order']),
                                     ('partner_id', '=', order.partner_id.id),
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
            return {'carrier_acc_no': False, 'error_message': order.delivery_message, 'new_amount_delivery': Monetary.value_to_html(order.amount_delivery, {'display_currency': currency}), 'status': order.delivery_rating_success}

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


