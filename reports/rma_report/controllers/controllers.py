# -*- coding: utf-8 -*-
from odoo import http

# class LotHistory(http.Controller):
#     @http.route('/lot_history/lot_history/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lot_history/lot_history/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lot_history.listing', {
#             'root': '/lot_history/lot_history',
#             'objects': http.request.env['lot_history.lot_history'].search([]),
#         })

#     @http.route('/lot_history/lot_history/objects/<model("lot_history.lot_history"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lot_history.object', {
#             'object': obj
#         })