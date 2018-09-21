# -*- coding: utf-8 -*-
from odoo import http

# class WebsiteQuoteExt(http.Controller):
#     @http.route('/website_quote_ext/website_quote_ext/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_quote_ext/website_quote_ext/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_quote_ext.listing', {
#             'root': '/website_quote_ext/website_quote_ext',
#             'objects': http.request.env['website_quote_ext.website_quote_ext'].search([]),
#         })

#     @http.route('/website_quote_ext/website_quote_ext/objects/<model("website_quote_ext.website_quote_ext"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_quote_ext.object', {
#             'object': obj
#         })