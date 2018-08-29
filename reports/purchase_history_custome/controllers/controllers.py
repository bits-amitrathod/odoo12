# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseHistoryCustome(http.Controller):
#     @http.route('/purchase_history_custome/purchase_history_custome/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_history_custome/purchase_history_custome/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_history_custome.listing', {
#             'root': '/purchase_history_custome/purchase_history_custome',
#             'objects': http.request.env['purchase_history_custome.purchase_history_custome'].search([]),
#         })

#     @http.route('/purchase_history_custome/purchase_history_custome/objects/<model("purchase_history_custome.purchase_history_custome"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_history_custome.object', {
#             'object': obj
#         })