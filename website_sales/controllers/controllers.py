# -*- coding: utf-8 -*-
from odoo import fields,http
from odoo.http import request
from addons.website_sale.controllers.main import WebsiteSale

class WebsiteSales(WebsiteSale):
    @http.route([
        '/shop',
        '/shop/featured',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if request.httprequest.path == "/shop/featured" :
            result = request.env['product.public.category'].search([('name','ilike', 'featured' )], limit=1)
            if result :
                category = result.id

        responce =  super(WebsiteSales,self).shop(page, category, search, ppg, **post)

        payload = responce.qcontext;
        irConfig = request.env['ir.config_parameter'].sudo();
        # and irConfig.get_param('stock.module_product_expiry')
        payload['isVisibleWebsiteExpirationDate'] = irConfig.get_param('website_sales.default_website_expiration_date')
        if payload['products'] and payload['isVisibleWebsiteExpirationDate']:
            productProduct = request.env['product.product'].search([('product_tmpl_id', 'in', payload['products'].ids)])

            productMaxMinDates = {}
            for val in productProduct:
                val.env.cr.execute(
                    "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = %s",(val.id,))
                query_result = val.env.cr.dictfetchone()
                productMaxMinDates[val.id] = {"min" : fields.Datetime.from_string(query_result['min']), "max": fields.Datetime.from_string(query_result['max'])}

            payload['productExpiration'] = productMaxMinDates;

        porductRows = [[]]
        i = 1
        for val in payload['products']:
            porductRows[-1].append(val)
            if i % 4 == 0:
                porductRows.append([])
            i += 1

        payload['porductRows'] = porductRows

        return request.render("website_sale.products", payload)

    @http.route(['/shop/cart/updatePurchaseOrderNumber'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, purchase_order, **kw):
        salesOrderContext = {
            'client_order_ref': purchase_order
        }

        value = {'success': request.env['sale.order'].sudo().browse(request.session['sale_order_id']).write(
            salesOrderContext)}

        return value

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        responce = super(WebsiteSales, self).product(product, category='', search='', **kwargs)
        payload = responce.qcontext;

        productMaxMinDates = {}
        request.env.cr.execute(
                "SELECT min(use_date), max (use_date) FROM public.stock_production_lot where product_id = %s",
                (payload['product'].product_variant_id.id,))
        query_result = request.env.cr.dictfetchone()
        productMaxMinDates[payload['product'].product_variant_id.id] = {"min": fields.Datetime.from_string(query_result['min']),
                                                          "max": fields.Datetime.from_string(query_result['max'])}

        payload['productExpiration'] = productMaxMinDates
        payload['userEmail'] = request.env.user.email
        payload['isVisibleWebsiteExpirationDate'] = request.env['ir.config_parameter'].sudo().get_param('website_sales.default_website_expiration_date')
        return request.render("website_sale.product", payload)




