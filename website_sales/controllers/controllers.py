# -*- coding: utf-8 -*-
import odoo
from odoo import fields, http
from odoo.http import request


class WebsiteSales(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route([
        '/shop',
        '/shop/featured',
        '/shop/capital-equipment',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if not 'order' in post:
            post.update({'order': 'name asc'})

        if request.httprequest.path == "/shop/featured":
            result = request.env['product.public.category'].search([('name', 'ilike', 'featured')], limit=1)
            if result:
                category = result.id

        if request.httprequest.path == "/shop/capital-equipment":
            result = request.env['product.public.category'].search([('name', 'ilike', 'capital equipment')], limit=1)
            if result:
                category = result.id

        responce = super(WebsiteSales, self).shop(page, category, search, ppg, **post)

        payload = responce.qcontext
        irConfig = request.env['ir.config_parameter'].sudo()
        payload['isVisibleWebsiteExpirationDate'] = irConfig.get_param('website_sales.default_website_expiration_date')
        if payload['products'] and payload['isVisibleWebsiteExpirationDate']:
            productProduct = request.env['product.product'].search([('product_tmpl_id', 'in', payload['products'].ids)])

            productMaxMinDates = {}
            for val in productProduct:
                if (val.actual_quantity) > 0:
                    query_result = self.fetch_lot_expirydates(val.id)
                    productMaxMinDates[val.id] = {"min": fields.Datetime.from_string(query_result['min']),
                                                  "max": fields.Datetime.from_string(query_result['max'])}
                else:
                    productMaxMinDates[val.id] = {
                        "min": None,
                        "max": None
                    }

            payload['productExpiration'] = productMaxMinDates

        porductRows = [[]]
        i = 1
        for val in payload['products']:
            porductRows[-1].append(val)
            if i % 4 == 0:
                porductRows.append([])
            i += 1

        payload['porductRows'] = porductRows

        return request.render("website_sale.products", payload)

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        responce = super(WebsiteSales, self).product(product, category='', search='', **kwargs)
        payload = responce.qcontext

        productMaxMinDates = {}
        if (payload['product'].actual_quantity) > 0:
            query_result = self.fetch_lot_expirydates(payload['product'].product_variant_id.id)
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": fields.Datetime.from_string(query_result['min']),
                "max": fields.Datetime.from_string(query_result['max'])
            }
        else:
            productMaxMinDates[payload['product'].product_variant_id.id] = {
                "min": None,
                "max": None
            }

        payload['productExpiration'] = productMaxMinDates
        payload['userEmail'] = request.env.user.email
        payload['isVisibleWebsiteExpirationDate'] = request.env['ir.config_parameter'].sudo().get_param(
            'website_sales.default_website_expiration_date')
        return request.render("website_sale.product", payload)

    def fetch_lot_expirydates(self, product_id):
        request.env.cr.execute(
            """SELECT
                sum(quantity), min(use_date), max(use_date)
            FROM
                stock_quant
            INNER JOIN
                stock_production_lot
            ON
                (
                    stock_quant.lot_id = stock_production_lot.id)
            INNER JOIN
                stock_location
            ON
                (
                    stock_quant.location_id = stock_location.id)
            WHERE
                stock_location.usage in('internal', 'transit') and stock_production_lot.product_id = %s """,
            (product_id,))
        return request.env.cr.dictfetchone()

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        responce = super(WebsiteSales, self).payment_confirmation(**post)
        responce.qcontext['order'].workflow_process_id = 1
        template = request.env.ref('website_sales.common_mail_template').sudo()
        template.send_mail(responce.qcontext['order'].id, force_send=True)
        return responce


class WebsiteSaleOptionsCstm(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route(['/shop/modal'], type='json', auth="public", methods=['POST'], website=True)
    def modal(self, product_id, **kw):
        pricelist = request.website.get_current_pricelist()
        product_context = dict(request.context)
        quantity = kw['kwargs']['context']['quantity']
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
        # fetch quantity from custom context
        product_context.update(kw.get('kwargs', {}).get('context', {}))

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: request.env['res.currency']._compute(from_currency, to_currency, price)
        product = request.env['product.product'].with_context(product_context).browse(int(product_id))

        main_product_attr_ids = self.get_attribute_value_ids(product)
        for variant in main_product_attr_ids:
            if variant[0] == product.id:
                # We indeed need a list of lists (even with only 1 element)
                main_product_attr_ids = [variant]
                break

        return request.env['ir.ui.view'].render_template("website_sales.modalCSTM", {
            'product': product,
            'quantity': quantity,
            'compute_currency': compute_currency,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'main_product_attr_ids': main_product_attr_ids,
        })
