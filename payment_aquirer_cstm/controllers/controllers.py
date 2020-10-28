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
                    order.state = 'sent'
                    if not order.client_order_ref:
                        if not order.x_studio_allow_duplicate_po:
                            result = request.env['sale.order'].sudo().search(
                                [('client_order_ref', '=', kwargs['purchase_order'])])
                            if result:
                                vals = {'error': "The PO number is already present on another Sales Order."}
                                return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)
                            else:
                                order.client_order_ref = kwargs['purchase_order']
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


    @http.route(['/shop/cart/expeditedShipping'], type='http', auth="public", methods=['POST'], website=True,
                csrf=False)
    def expedited_shipping(self, expedited_shipping, **kw):
        request.session['expedited_shipping'] = expedited_shipping
        return request.redirect('/shop/payment')

    @http.route('/checkHavingCarrierWithAccountNo', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def check_having_carrier_with_account_no(self, customerId):
        print('In check_having_carrier_with_account_no')
        res_partner = request.env['res.partner'].sudo().search([('id', '=', customerId)])
        if res_partner.having_carrier and res_partner.carrier_acc_no:
            return {'client_order_ref_error': 'account no present'}
        else:
            return {'client_order_ref_error': 'Account no not present'}


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
                    ctx['freeShipingLabel'] = "delivery_" + str(x.id)
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
                ctx['freeShipingLabel'] = "delivery_"+str(x.id)
            break

        return responce

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        responce = super(WebsiteSalesPaymentAquirerCstm, self).payment_confirmation(**post)
        order = responce.qcontext['order']

        if 'expedited_shipping' in request.session:
            expedited_shipping = request.session['expedited_shipping']
            if expedited_shipping:
                order.sudo().write({'sale_note': expedited_shipping})
                #order_sudo = self._document_check_access('sale.order', order.id, access_token=order.access_token)
                # _message_post_helper(res_model='sale.order', res_id=order.id,
                #                      message="<strong>Expedited Shipping:</strong> " + expedited_shipping,
                #                      token=order.access_token,
                #                      message_type='notification', subtype="mail.mt_note",
                #                      partner_ids=order.user_id.sudo().partner_id.ids)
                request.session['expedited_shipping'] = ""

        return responce


