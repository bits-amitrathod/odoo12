# -*- coding: utf-8 -*-
from odoo import http

# class MultiBarcode(http.Controller):
#     @http.route('/multi_barcode/multi_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/multi_barcode/multi_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('multi_barcode.listing', {
#             'root': '/multi_barcode/multi_barcode',
#             'objects': http.request.env['multi_barcode.multi_barcode'].search([]),
#         })

#     @http.route('/multi_barcode/multi_barcode/objects/<model("multi_barcode.multi_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('multi_barcode.object', {
#             'object': obj
#         })