# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

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

    @http.route('/vendor_offer/accept/',  type='http', auth="public", website=True, csrf=False)
    def vendor_offer_accept(self,product_id,**kw):
        val = request.vendorOffer.action_button_confirm_api(product_id)
        return "accepted"


    @http.route('/vendor_offer/reject/', type='http', auth="public", website=True, csrf=False)
    def vendor_offer_reject(self,product_id,**kw):
        val = request.vendorOffer.action_cancel_vendor_offer_api(product_id)
        return "rejected"