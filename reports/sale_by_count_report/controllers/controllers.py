# -*- coding: utf-8 -*-
from odoo import http

# class SaleByCountReport(http.Controller):
#     @http.route('/sale_by_count_report/sale_by_count_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_by_count_report/sale_by_count_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_by_count_report.listing', {
#             'root': '/sale_by_count_report/sale_by_count_report',
#             'objects': http.request.env['sale_by_count_report.sale_by_count_report'].search([]),
#         })

#     @http.route('/sale_by_count_report/sale_by_count_report/objects/<model("sale_by_count_report.sale_by_count_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_by_count_report.object', {
#             'object': obj
#         })