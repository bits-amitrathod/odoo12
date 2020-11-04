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

    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('sps_theme.home_page_template')

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

    @http.route('/equipment-sell', type='http', auth="public", website=True)
    def seller(self):
        return http.request.render('sps_theme.equipment_sell_template')

    @http.route('/request-a-quote', type='http', auth="public", website=True)
    def request_a_quote(self):
        return http.request.render('sps_theme.request_a_quote_template')

    @http.route('/thank-you', type='http', auth="public", website=True)
    def thank_you(self):
        return http.request.render('sps_theme.thank_you_page_template')

    @http.route('/surgical-products-sell', type='http', auth="public", website=True)
    def surgical_products_sell(self):
        return http.request.render('sps_theme.surgical_products_sell_page_template')
