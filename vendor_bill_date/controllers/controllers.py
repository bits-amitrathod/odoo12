# -*- coding: utf-8 -*-
from odoo import http

class SpsBillDate(http.Controller):
    @http.route('/vendor_bill_date/vendor_bill_date/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/vendor_bill_date/vendor_bill_date/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('vendor_bill_date.listing', {
            'root': '/vendor_bill_date/vendor_bill_date',
            'objects': http.request.env['vendor_bill_date.vendor_bill_date'].search([]),
        })

    @http.route('/vendor_bill_date/vendor_bill_date/objects/<model("vendor_bill_date.vendor_bill_date"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('vendor_bill_date.object', {
            'object': obj
        })