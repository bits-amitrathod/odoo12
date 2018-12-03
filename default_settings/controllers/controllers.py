# -*- coding: utf-8 -*-
from odoo import http

# class DefaultSettings(http.Controller):
#     @http.route('/default_settings/default_settings/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/default_settings/default_settings/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('default_settings.listing', {
#             'root': '/default_settings/default_settings',
#             'objects': http.request.env['default_settings.default_settings'].search([]),
#         })

#     @http.route('/default_settings/default_settings/objects/<model("default_settings.default_settings"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('default_settings.object', {
#             'object': obj
#         })