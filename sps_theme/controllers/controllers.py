# -*- coding: utf-8 -*-
import base64
import werkzeug.wrappers
import os
# from addons.auth_signup.controllers.main import AuthSignupHome

from odoo import fields, http, modules, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content
from odoo.addons.portal.controllers.web import Home
from odoo.addons.http_routing.models.ir_http import slug, _guess_mimetype


class ThemeController(http.Controller):

    @http.route('/aboutus', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('sps_theme.about_page_template')

    @http.route('/contactus', type='http', auth="public", website=True)
    def contact(self):
        return http.request.render('sps_theme.contact_page_template')

    @http.route('/stockhawk', type='http', auth="public", website=True)
    def stockhawk(self):
        return http.request.render('sps_theme.stockhawk_page_template')

    @http.route('/careers', type='http', auth="public", website=True)
    def careers(self):
        return http.request.render('sps_theme.careers_page_template')

    @http.route('/faqs', type='http', auth="public", website=True)
    def faqs(self):
        return http.request.render('sps_theme.faqs_page_template')