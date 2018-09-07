# -*- coding: utf-8 -*-
from odoo import http

# class ProductExpiryExtension(http.Controller):
#     @http.route('/product_expiry_extension/product_expiry_extension/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_expiry_extension/product_expiry_extension/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_expiry_extension.listing', {
#             'root': '/product_expiry_extension/product_expiry_extension',
#             'objects': http.request.env['product_expiry_extension.product_expiry_extension'].search([]),
#         })

#     @http.route('/product_expiry_extension/product_expiry_extension/objects/<model("product_expiry_extension.product_expiry_extension"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_expiry_extension.object', {
#             'object': obj
#         })