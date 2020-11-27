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


class WebsiteCstm(http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('website_cstm.home_page')

    @http.route('/about-us', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('website_cstm.about_page')


    @http.route('/repair-1', type='http', auth="public", website=True)
    def repair(self):
        return http.request.render('website_cstm.repair_page')

    @http.route('/sell-form', type='http', auth="public", website=True)
    def seller(self):
        return http.request.render('website_cstm.seller_page')

    @http.route('/equipment', type='http', auth="public", website=True)
    def equipment(self):
        return http.request.render('website_cstm.equipment_page')

    @http.route('/purchase-product', type='http', auth="public", website=True)
    def purchase_product(self):
        return http.request.render('website_cstm.purchase_product_page')

    @http.route('/vendor-list', type='http', auth="public", website=True)
    def vendor_list(self):
        return http.request.render('website_cstm.vendor_list_page')

    @http.route('/equipment-service-request-form', type='http', auth="public", website=True)
    def equipment_service_request(self):
        return http.request.render('website_cstm.equipment_service_page')

    @http.route('/why-you-need-us', type='http', auth="public", website=True)
    def need_us(self):
        return http.request.render('website_cstm.need_page')

    @http.route('/faqs', type='http', auth="public", website=True)
    def faqs(self):
        return http.request.render('website_cstm.faqs_page')

    @http.route('/quality_assurance', type='http', auth="public", website=True)
    def quality_assurance_page(self):
        return http.request.render('website_cstm.qualityassurance_page')

    @http.route('/search', type='http', auth="public", website=True)
    def search(self):
        return http.request.render('website_cstm.search_page')

    @http.route('/terms_of_sale', type='http', auth="public", website=True)
    def terms_of_sale(self):
        return http.request.render('website_cstm.terms_of_sale')

    @http.route('/terms_of_purchase', type='http', auth="public", website=True)
    def terms_of_purchase(self):
        return http.request.render('website_cstm.terms_of_purchase')

    @http.route('/stockhawk', type='http', auth="public", website=True)
    def stockhawk(self):
        return http.request.render('website_cstm.stockhawk_page')

    @http.route('/sell-buy-back', type='http', auth="public", website=True)
    def sell(self):
        return http.request.render('website_cstm.sell_page')

    @http.route('/request-a-quote', type='http', auth="public", website=True)
    def request_a_quote(self):
        return http.request.render('website_cstm.request_quote_page')

    @http.route('/careers', type='http', auth="public", website=True)
    def careers(self):
        return http.request.render('website_cstm.careers_page')

    @http.route('/our-mission', type='http', auth="public", website=True)
    def mission(self):
        return http.request.render('website_cstm.mission_page')

    @http.route('/testimonials', type='http', auth="public", website=True)
    def testimonials(self):
        return http.request.render('website_cstm.testimonials_page')

    @http.route('/thank-you', type='http', auth="public", website=True)
    def testimonials(self):
        return http.request.render('website_cstm.thank-you')

    @http.route('/contactus', type='http', auth="public", website=True)
    def contactus(self):
        return http.request.render('website_cstm.contactus_form')

    @http.route('/product_types', type='http', auth="public", website=True)
    def product_types_page(self):
        values = {"categories": request.env['product.public.category'].search([('parent_id', '=', False)])}
        return http.request.render('website_cstm.product_types_page', values)

    @http.route('/notifyme', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def notifyme(self, product_id, email):
        StockNotifcation = request.env['website_cstm.product_instock_notify'].sudo()
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

    @http.route('/downloadCatalog', type='http', auth="public", website=True)
    def downloadCatalog(self):
        result = request.env['website_cstm.product_download_catelog'].search([('status', '=', 'active')], limit=1)
        if result:
            id = result.id

            status, headers, content = binary_content(model='website_cstm.product_download_catelog', id=id, field='file',
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

# class AuthSignupHomeCstm(AuthSignupHome):
#     @http.route(['/web/signup'], type='http', auth='public', website=True, sitemap=False)
#     def web_auth_signup(self, *args, **kw):
#         responce = super(AuthSignupHome, self).shop(*args, **kw)
#         return responce


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
