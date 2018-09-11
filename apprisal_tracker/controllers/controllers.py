# -*- coding: utf-8 -*-
from odoo import http

class ApprisalTracker(http.Controller):
    @http.route('/apprisal_tracker/apprisal_tracker/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/apprisal_tracker/apprisal_tracker/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('apprisal_tracker.listing', {
            'root': '/apprisal_tracker/apprisal_tracker',
            'objects': http.request.env['apprisal_tracker.apprisal_tracker'].search([]),
        })

    @http.route('/apprisal_tracker/apprisal_tracker/objects/<model("apprisal_tracker.apprisal_tracker"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('apprisal_tracker.object', {
            'object': obj
        })