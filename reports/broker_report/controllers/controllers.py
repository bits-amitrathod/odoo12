# -*- coding: utf-8 -*-
from odoo import http

# class BrokerReport(http.Controller):
#     @http.route('/broker_report/broker_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/broker_report/broker_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('broker_report.listing', {
#             'root': '/broker_report/broker_report',
#             'objects': http.request.env['broker_report.broker_report'].search([]),
#         })

#     @http.route('/broker_report/broker_report/objects/<model("broker_report.broker_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('broker_report.object', {
#             'object': obj
#         })