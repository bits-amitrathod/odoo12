# -*- coding: utf-8 -*-
from odoo import http

# class TrendingReport(http.Controller):
#     @http.route('/trending_report/trending_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/trending_report/trending_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('trending_report.listing', {
#             'root': '/trending_report/trending_report',
#             'objects': http.request.env['trending_report.trending_report'].search([]),
#         })

#     @http.route('/trending_report/trending_report/objects/<model("trending_report.trending_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('trending_report.object', {
#             'object': obj
#         })