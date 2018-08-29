# -*- coding: utf-8 -*-
from odoo import http

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