# -*- coding: utf-8 -*-
import odoo
from odoo import fields, http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteSales(odoo.addons.website_sale.controllers.main.WebsiteSale):
    @http.route([
        '/shop',
        '/shop/featured',
        '/shop/capital-equipment',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>/brand/<model("product.brand"):brand>',
        '/shop/category/<model("product.public.category"):category>/brand/<model("product.brand"):brand>/page/<int:page>',
        '/shop/brand/<model("product.brand"):brand>',
        '/shop/brand/<model("product.brand"):brand>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None,search='', brand= None, ppg=False, **post):
        product_template = request.env['product.template'].search([('actual_quantity', '=', False)])
        product_brands = []

        title = "Shop"

        if request.httprequest.path == "/shop":
            product_brands = []

        if len(product_template)>0:
            for product in product_template:
                product.update({'actual_quantity':0})

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = 20

        if not 'order' in post:
            post.update({'order': 'actual_quantity desc'})

        if request.httprequest.path == "/shop/featured":
            title = "Sale Items"
            result = request.env['product.public.category'].search([('name', 'ilike', 'featured')], limit=1)
            if result:
                category = result

        if request.httprequest.path == "/shop/capital-equipment":
            result = request.env['product.public.category'].search([('name', 'ilike', 'capital equipment')], limit=1)
            if result:
                category = result

        #  after category id Found the find Brand List
        if category:
            s = str(category) if isinstance(category, str) else str(category.id)
            request.env.cr.execute("SELECT product_template_id FROM product_public_category_product_template_rel where product_public_category_id = "+ s)
            r = request.env.cr.fetchall()
            pt_list = request.env['product.template'].sudo().search([('id', 'in', r)])
            for b in pt_list:
                if b.product_brand_id:
                    if not b.product_brand_id in product_brands:
                        product_brands.append(b.product_brand_id)

        responce = super(WebsiteSales, self).shop(page, category, search, None, **post)

        payload = responce.qcontext

        if brand:
            search_product =[]
            url = "/shop/category/"+slug(category)+"/brand/%s" % slug(brand)
            if category:
                request.env.cr.execute(
                    "SELECT product_template_id FROM product_public_category_product_template_rel where product_public_category_id = " + str(
                        category.id))
                r = request.env.cr.fetchall()
                pt_list_b = request.env['product.template'].sudo().search([('id', 'in', r),('product_brand_id','=',brand.id)])
            search_product = pt_list_b
            product_count = len(search_product)
            pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
            payload['pager'] = pager
            offset = pager['offset']
            products = search_product[offset: offset + ppg]
            payload['products'] = products

        irConfig = request.env['ir.config_parameter'].sudo()
        payload['isVisibleWebsiteExpirationDate'] = irConfig.get_param('website_sales.website_expiration_date')
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
            # if i % 4 == 0:
            #     porductRows.append([])
            # i += 1

        payload['porductRows'] = porductRows
        payload['brands'] = product_brands
        payload['title'] = title
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
            'website_sales.website_expiration_date')
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
        order = responce.qcontext['order']
        order.workflow_process_id = 1

        template = request.env.ref('website_sales.website_order_placed').sudo()

        if request.env.user.user_id.id and not request.env.user.user_id.id == order.user_id.id:
            order.user_id = request.env.user.user_id

        template.send_mail(order.id, force_send=True)
        msg = "Quotation Email Sent to: " + order.user_id.login
        order.message_post(body=msg)


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
