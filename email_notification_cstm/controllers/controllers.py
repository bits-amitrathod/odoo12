# -*- coding: utf-8 -*-
from odoo import http

# class EmailNotificationCstm(http.Controller):
#     @http.route('/email_notification_cstm/email_notification_cstm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/email_notification_cstm/email_notification_cstm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('email_notification_cstm.listing', {
#             'root': '/email_notification_cstm/email_notification_cstm',
#             'objects': http.request.env['email_notification_cstm.email_notification_cstm'].search([]),
#         })

#     @http.route('/email_notification_cstm/email_notification_cstm/objects/<model("email_notification_cstm.email_notification_cstm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('email_notification_cstm.object', {
#             'object': obj
#         })