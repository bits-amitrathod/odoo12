# -*- coding: utf-8 -*-
from odoo import http

# class TpsReportSale(http.Controller):
#     @http.route('/tps_report_sale/tps_report_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tps_report_sale/tps_report_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tps_report_sale.listing', {
#             'root': '/tps_report_sale/tps_report_sale',
#             'objects': http.request.env['tps_report_sale.tps_report_sale'].search([]),
#         })

#     @http.route('/tps_report_sale/tps_report_sale/objects/<model("tps_report_sale.tps_report_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tps_report_sale.object', {
#             'object': obj
#         })