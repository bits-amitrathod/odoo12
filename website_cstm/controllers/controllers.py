# -*- coding: utf-8 -*-
import base64
import werkzeug.wrappers
# from addons.auth_signup.controllers.main import AuthSignupHome

from odoo import fields, http, modules, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content


class WebsiteCstm(http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('website_cstm.home_page')

    @http.route('/about-us', type='http', auth="public", website=True)
    def about(self):
        return http.request.render('website_cstm.about_page')

    @http.route('/faqs', type='http', auth="public", website=True)
    def faqs(self):
        return http.request.render('website_cstm.faqs_page')

    @http.route('/quality_assurance', type='http', auth="public", website=True)
    def quality_assurance_page(self):
        return http.request.render('website_cstm.qualityassurance_page')

    @http.route('/search', type='http', auth="public", website=True)
    def search(self):
        return http.request.render('website_cstm.search_page')

    @http.route('/terms', type='http', auth="public", website=True)
    def terms(self):
        return http.request.render('website_cstm.terms')

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
