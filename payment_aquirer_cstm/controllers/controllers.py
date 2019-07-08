# -*- coding: utf-8 -*-
import odoo
from odoo import http
from odoo.http import request


class PaymentAquirerCstm(http.Controller):

    @http.route('/shop/payment/purchaseorderform', type='http', auth="public", website=True, csrf=False)
    def purchase_order_form_validate(self, **kwargs):
        vals = {}
        if kwargs:
            order = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
            if order.client_order_ref:
                kwargs['purchase_order'] = order.client_order_ref

            if 'purchase_order' in kwargs and kwargs['purchase_order'] != '':
                tx_id = request.session.get('sale_transaction_id')
                if tx_id:
                    transaction = request.env['payment.transaction'].sudo().browse(tx_id)
                    transaction.state = 'pending'
                    order.state = 'sent'
                    if not order.client_order_ref:
                        order.client_order_ref = kwargs['purchase_order']
                    return request.redirect('/shop/payment/validate')
                else:
                    request.redirect('/shop')
            if 'return_url' not in kwargs:
                vals = {'error': "Please enter Purchase order"}
        return http.request.render('payment_aquirer_cstm.purchase_order_page', vals)

    @http.route(['/shop/cart/updatePurchaseOrderNumber'], type='json', auth="public", methods=['POST'], website=True,
                csrf=False)
    def cart_update(self, purchase_order, **kw):

        order = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
        order.client_order_ref = purchase_order
        value = {'success': True}

        return value


class WebsiteSales(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        # deliveryResponce = WebsiteSaleDelivery().payment(**post)
        responce = super(WebsiteSales, self).payment(**post)
        # responce.qcontext.update(deliveryResponce.qcontext)

        ctx = responce.qcontext
        if not ctx['order'].partner_id.allow_purchase:
            for x in ctx['acquirers']:
                if x.name == 'Purchase Order':
                    ctx['acquirers'].remove(x)

        return responce
