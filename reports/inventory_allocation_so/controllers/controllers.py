# -*- coding: utf-8 -*-
from odoo import http

# class InventoryAllocationForSo(http.Controller):
#     @http.route('/inventory__allocation__for__so/inventory__allocation__for__so/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inventory__allocation__for__so/inventory__allocation__for__so/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inventory__allocation__for__so.listing', {
#             'root': '/inventory__allocation__for__so/inventory__allocation__for__so',
#             'objects': http.request.env['inventory__allocation__for__so.inventory__allocation__for__so'].search([]),
#         })

#     @http.route('/inventory__allocation__for__so/inventory__allocation__for__so/objects/<model("inventory__allocation__for__so.inventory__allocation__for__so"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inventory__allocation__for__so.object', {
#             'object': obj
#         })