# -*- coding: utf-8 -*-
from odoo import http

# class TestExample(http.Controller):
#     @http.route('/test_example/test_example/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/test_example/test_example/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('test_example.listing', {
#             'root': '/test_example/test_example',
#             'objects': http.request.env['test_example.test_example'].search([]),
#         })

#     @http.route('/test_example/test_example/objects/<model("test_example.test_example"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('test_example.object', {
#             'object': obj
#         })