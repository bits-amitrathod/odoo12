# -*- coding: utf-8 -*-
import base64
import werkzeug.wrappers
import os
# from addons.auth_signup.controllers.main import AuthSignupHome

from odoo import fields, http, modules, SUPERUSER_ID
from odoo.http import request
# from odoo.addons.web.controllers.main import binary_content
from odoo.addons.portal.controllers.web import Home
from odoo.addons.http_routing.models.ir_http import slug, _guess_mimetype


class ThemeController(http.Controller):

    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('sps_theme.home_page_template')

    @http.route('/aboutus', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('sps_theme.about_page_template')

    @http.route('/our-team', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('sps_theme.our_team_page_template')

    @http.route('/contact-us', type='http', auth="public", website=True)
    def contact(self):
        return http.request.render('sps_theme.contact_page_template1')

    @http.route('/stockhawk', type='http', auth="public", website=True)
    def stockhawk(self):
        return http.request.render('sps_theme.stockhawk_page_template1')

    @http.route('/careers', type='http', auth="public", website=True)
    def careers(self):
        return http.request.render('sps_theme.careers_page_template1')

    @http.route('/faqs', type='http', auth="public", website=True)
    def faqs(self):
        return http.request.render('sps_theme.faqs_page_template')

    @http.route('/equipment-sell', type='http', auth="public", website=True)
    def seller(self):
        return http.request.render('sps_theme.equipment_sell_template1')

    @http.route('/request-a-quote', type='http', auth="public", website=True)
    def request_a_quote(self):
        return http.request.render('sps_theme.request_a_quote_template')

    @http.route('/thank-you', type='http', auth="public", website=True)
    def thank_you(self):
        return http.request.render('sps_theme.thank_you_page_template')

    @http.route('/surgical-products-sell', type='http', auth="public", website=True)
    def surgical_products_sell(self):
        return http.request.render('sps_theme.surgical_products_sell_page_template12')

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

    @http.route('/vendor-list', type='http', auth="public", website=True)
    def vendor_list_method(self):
        return http.request.render('sps_theme.vendor_list_template')

    @http.route('/seller-form', type='http', auth="public", website=True)
    def seller_form_method(self):
        return http.request.render('sps_theme.seller_form_template')

    @http.route('/terms_of_sale', type='http', auth="public", website=True)
    def terms_of_sale(self):
        return http.request.render('sps_theme.terms_of_sales_template')

    @http.route('/terms_of_purchase', type='http', auth="public", website=True)
    def terms_of_purchase(self):
        return http.request.render('sps_theme.terms_of_purchase_template')

    @http.route('/downloadCatalog', type='http', auth="public", website=True)
    def downloadCatalog(self):
        result = request.env['sps_theme.product_download_catelog'].search([('status', '=', 'active')], limit=1)
        if result:
            id = result.id

            status, headers, content = request.env['ir.http'].binary_content(model='sps_theme.product_download_catelog',
                                                                             id=id,
                                                                             field='file',
                                                                             filename_field='filename',
                                                                             download=True)

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

    @http.route('/notifyme', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def notifyme(self, product_id, email):
        StockNotifcation = request.env['sps_theme.product_instock_notify'].sudo()
        isSubcribed = StockNotifcation.search([
            ('product_tmpl_id', '=', int(product_id)),
            ('email', '=', email.lower()),
            ('status', '=', 'pending'),
        ], limit=1)
        if not isSubcribed:
            StockNotifcation.create({'status': 'pending', 'email': email.lower(), 'product_tmpl_id': product_id})
            return True
        else:
            return False


class Website(Home):
    @http.route(['/website/add/', '/website/add/<path:path>'], type='http', auth="user", website=True)
    def pagenew(self, path="", noredirect=False, add_menu=False, template=False, **kwargs):
        # for supported mimetype, get correct default template
        _, ext = os.path.splitext(path)
        ext_special_case = ext and ext in _guess_mimetype() and ext != '.html'

        if not template and ext_special_case:
            default_templ = 'website.default_%s' % ext.lstrip('.')
            if request.env.ref(default_templ, False):
                template = default_templ

        template = template and dict(template=template) or {}
        page = request.env['website'].new_page_test(path, add_menu=add_menu, **template)
        url = page['url']
        if noredirect:
            return werkzeug.wrappers.Response(url, mimetype='text/plain')

        if ext_special_case:  # redirect non html pages to backend to edit
            return werkzeug.utils.redirect('/web#id=' + str(page.get('view_id')) + '&view_type=form&model=ir.ui.view')
        return werkzeug.utils.redirect(url + "?enable_editor=1")
