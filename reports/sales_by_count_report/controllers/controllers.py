# -*- coding: utf-8 -*-
from odoo import http

# class SaleByCountReport(http.Controller):
#     @http.route('/sales_by_count_report/sales_by_count_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_by_count_report/sales_by_count_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_by_count_report.listing', {
#             'root': '/sales_by_count_report/sales_by_count_report',
#             'objects': http.request.env['sales_by_count_report.sales_by_count_report'].search([]),
#         })

#     @http.route('/sales_by_count_report/sales_by_count_report/objects/<model("sales_by_count_report.sales_by_count_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_by_count_report.object', {
#             'object': obj
#         })