# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
import base64

class VendorOffer(http.Controller):
    @http.route('/vendor_offer/vendor_offer/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/vendor_offer/vendor_offer/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('vendor_offer.listing', {
            'root': '/vendor_offer/vendor_offer',
            'objects': http.request.env['vendor_offer.vendor_offer'].search([]),
        })

    @http.route('/vendor_offer/vendor_offer/objects/<model("vendor_offer.vendor_offer"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('vendor_offer.object', {
            'object': obj
        })

    @http.route('/vendor_offer/accept/',  type='json', auth="public", website=True, csrf=False)
    def vendor_offer_accept(self, res_id, order_id=None, partner_name=None, signature=None,access_token=None):
        order = request.env['purchase.order'].search([('id', '=', res_id)])
        if order.state == 'purchase':
            return {
                'error': _('Offer already Accepted'),
            }
        if order.state == 'cancel':
            return {
                'error': _('Offer already Rejected'),
            }
        order_sudo = order.sudo()
        if not signature:
            return {'error': _('Signature is missing.')}
        val = order_sudo.action_button_confirm_api_cash(res_id)
        _message_post_helper(
            res_model='purchase.order',
            res_id=order_sudo.id,
            message=_('Order signed by %s') % (partner_name,),
            attachments=[('signature.png', base64.b64decode(signature))] if signature else [],
            **({'token': access_token} if access_token else {}))
        return {
            'success': _('Your Order has been confirmed.'),
            'redirect_url': '/my/home',
        }

    @http.route('/vendor_offer/acceptcredit/', type='json', auth="public", website=True, csrf=False)
    def vendor_offer_accept_credit(self, res_id, order_id=None, partner_name=None, signature=None, access_token=None):
        order = request.env['purchase.order'].search([('id', '=', res_id)])
        if order.state == 'purchase':
            return {
                'error': _('Offer already Accepted'),
            }
        if order.state == 'cancel':
            return {
                'error': _('Offer already Rejected'),
            }
        order_sudo = order.sudo()
        if not signature:
            return {'error': _('Signature is missing.')}
        val = order_sudo.action_button_confirm_api_credit(res_id)
        _message_post_helper(
            res_model='purchase.order',
            res_id=order_sudo.id,
            message=_('Order signed by %s') % (partner_name,),
            attachments=[('signature.png', base64.b64decode(signature))] if signature else [],
            **({'token': access_token} if access_token else {}))
        return {
            'success': _('Your Order has been confirmed.'),
            'redirect_url': '/my/home',
        }


    @http.route('/vendor_offer/reject/', type='json', auth="public", website=True, csrf=False)
    def vendor_offer_reject(self, res_id,order_id=None, partner_name=None, signature=None,access_token=None):
        if not signature:
            return {'error': _('Signature is missing.')}
        order = request.env['purchase.order'].browse(res_id)
        if order.state == 'purchase':
            return {
                'error': _('Offer already Accepted'),
            }
        if order.state == 'cancel':
            return {
                'error': _('Offer already Rejected'),
            }
        order_sudo = order.sudo()
        val = order_sudo.action_cancel_vendor_offer_api(res_id)
        _message_post_helper(
            res_model='purchase.order',
            res_id=order_sudo.id,
            message=_('Order rejected by %s') % (partner_name,),
            attachments=[('signature.png', base64.b64decode(signature))] if signature else [],
            **({'token': access_token} if access_token else {}))
        return {
            'success': _('Your Order has been rejected.'),
            'redirect_url': '/my/home',
        }