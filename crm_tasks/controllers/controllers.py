# -*- coding: utf-8 -*-
from odoo import http

# class CrmActivity(http.Controller):
#     @http.route('/crm_tasks/crm_tasks/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/crm_tasks/crm_tasks/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('crm_tasks.listing', {
#             'root': '/crm_tasks/crm_tasks',
#             'objects': http.request.env['crm_tasks.crm_tasks'].search([]),
#         })

#     @http.route('/crm_tasks/crm_tasks/objects/<model("crm_tasks.crm_tasks"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('crm_tasks.object', {
#             'object': obj
#         })