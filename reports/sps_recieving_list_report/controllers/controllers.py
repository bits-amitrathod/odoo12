# -*- coding: utf-8 -*-
from odoo import http

# class InventoryAdjustmentReport(http.Controller):
#     @http.route('/inventory_adjustment_report/inventory_adjustment_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inventory_adjustment_report/inventory_adjustment_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inventory_adjustment_report.listing', {
#             'root': '/inventory_adjustment_report/inventory_adjustment_report',
#             'objects': http.request.env['inventory_adjustment_report.inventory_adjustment_report'].search([]),
#         })

#     @http.route('/inventory_adjustment_report/inventory_adjustment_report/objects/<model("inventory_adjustment_report.inventory_adjustment_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inventory_adjustment_report.object', {
#             'object': obj
#         })