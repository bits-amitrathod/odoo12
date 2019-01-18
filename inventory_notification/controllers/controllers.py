# -*- coding: utf-8 -*-
from odoo import http

# class BitsScrap(http.Controller):
#     @http.route('/bits_scrap/bits_scrap/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bits_scrap/bits_scrap/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bits_scrap.listing', {
#             'root': '/bits_scrap/bits_scrap',
#             'objects': http.request.env['bits_scrap.bits_scrap'].search([]),
#         })

#     @http.route('/bits_scrap/bits_scrap/objects/<model("bits_scrap.bits_scrap"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bits_scrap.object', {
#             'object': obj
#         })