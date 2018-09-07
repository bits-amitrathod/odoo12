# -*- coding: utf-8 -*-
from odoo import http

# class VendorOfferAutomation(http.Controller):
#     @http.route('/vendor_offer_automation/vendor_offer_automation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vendor_offer_automation/vendor_offer_automation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vendor_offer_automation.listing', {
#             'root': '/vendor_offer_automation/vendor_offer_automation',
#             'objects': http.request.env['vendor_offer_automation.vendor_offer_automation'].search([]),
#         })

#     @http.route('/vendor_offer_automation/vendor_offer_automation/objects/<model("vendor_offer_automation.vendor_offer_automation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vendor_offer_automation.object', {
#             'object': obj
#         })