# -*- coding: utf-8 -*-
from odoo import http

# class Reports(http.Controller):
#     @http.route('/reports/reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reports/reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('reports.listing', {
#             'root': '/reports/reports',
#             'objects': http.request.env['reports.reports'].search([]),
#         })

#     @http.route('/reports/reports/objects/<model("reports.reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reports.object', {
#             'object': obj
#         })