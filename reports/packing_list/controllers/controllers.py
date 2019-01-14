# -*- coding: utf-8 -*-
from odoo import http

# class InventoryMonitor(http.Controller):
#     @http.route('/inventory_monitor/inventory_monitor/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inventory_monitor/inventory_monitor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inventory_monitor.listing', {
#             'root': '/inventory_monitor/inventory_monitor',
#             'objects': http.request.env['inventory_monitor.inventory_monitor'].search([]),
#         })

#     @http.route('/inventory_monitor/inventory_monitor/objects/<model("inventory_monitor.inventory_monitor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inventory_monitor.object', {
#             'object': obj
#         })