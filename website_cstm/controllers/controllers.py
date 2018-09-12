# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WebsiteCstm(http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def home(self, **kw):
        return http.request.render('website_cstm.home_page')

    # @http.route('/contactus', type='http', auth="public", website=True)
    # def contact(self):
    #     return http.request.render('website_cstm.contact_page')

    @http.route('/about', type='http', auth="public", website=True)
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

    @http.route('/product_types', type='http', auth="public", website=True)
    def product_types_page(self):
        values = {"categories": request.env['product.public.category'].search([('parent_id', '=', False)])}
        return http.request.render('website_cstm.product_types_page', values)

    @http.route('/notifyme', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def notifyme(self, product_id, email):
        StockNotifcation = request.env['website_cstm.product_instock_notify'].sudo()
        isSubcribed = StockNotifcation.search([
            ('product_tmpl_id', '=', int(product_id)),
            ('email', '=', email),
            ('status', '=', 'pending'),
        ], limit=1)
        if not isSubcribed:
            StockNotifcation.create({'status': 'pending', 'email': email, 'product_tmpl_id': product_id})
            return True
        else:
            return False
