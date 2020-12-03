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

    @http.route('/contact-us', type='http', auth="public", website=True)
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

    @http.route('/equipment-repair', type='http', auth="public", website=True)
    def equipment_repair_and_service(self):
        return http.request.render('sps_theme.equipment_repair_and_service_page_template')

    @http.route('/equipment-repair-service', type='http', auth="public", website=True)
    def equipment_repair_service(self):
        return http.request.render('sps_theme.equipment_service_request_form_template')

    @http.route('/terms-and-condition', type='http', auth="public", website=True)
    def terms_and_condition_policy(self):
        return http.request.render('sps_theme.terms_and_conditions_template')

    @http.route('/policy', type='http', auth="public", website=True)
    def policy(self):
        return http.request.render('sps_theme.policy_template')

    @http.route('/quality_assurance', type='http', auth="public", website=True)
    def quality_assurance_method(self):
        return http.request.render('sps_theme.quality_assurance_template')

    @http.route('/downloadCatalog', type='http', auth="public", website=True)
    def downloadCatalog(self):
        result = request.env['sps_theme.product_download_catelog'].search([('status', '=', 'active')], limit=1)
        if result:
            id = result.id

            status, headers, content = binary_content(model='sps_theme.product_download_catelog', id=id,
                                                      field='file',
                                                      filename_field='filename',
                                                      download=True, env=request.env(user=SUPERUSER_ID))

            if not content:
                img_path = modules.get_module_resource('web', 'static/src/img', 'placeholder.png')
                with open(img_path, 'rb') as f:
                    image = f.read()
                content = base64.b64encode(image)
            if status == 304:
                return werkzeug.wrappers.Response(status=304)
            image_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(image_base64)))
            response = request.make_response(image_base64, headers)
            response.status = str(status)
            return response
        raise werkzeug.exceptions.NotFound()