# -*- coding: utf-8 -*-
from odoo import http

class CustomerSps(http.Controller):
    @http.route('/customer_sps/customer_sps/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/customer_sps/customer_sps/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('customer_sps.listing', {
            'root': '/customer_sps/customer_sps',
            'objects': http.request.env['customer_sps.customer_sps'].search([]),
        })

    @http.route('/customer_sps/customer_sps/objects/<model("customer_sps.customer_sps"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('customer_sps.object', {
            'object': obj
        })