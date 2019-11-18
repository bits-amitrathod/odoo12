# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################
import logging

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug, slugify
from odoo.http import request
import re
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WebsiteRedirect(models.Model):
    _inherit = "website.redirect"

    def _get_rewrites(self):
        return [('custom', 'Custom'), ('product.template', 'Product'), ('product.public.category', 'Category')]
    _rewrite_selection = lambda self, * \
        args, **kwargs: self._get_rewrites(*args, **kwargs)

    rewrite_val = fields.Selection(
        string='Create URL Rewrite',
        selection=_rewrite_selection,
        help="Name of model for rewrite management. ex : [('model.model', 'Model')]",
        default='custom'
        )
    create_type = fields.Selection(
        string='Type',
        selection=[('custom', 'Custom'), ('system', 'System')],
        help="Rewrite record create from",
        default='custom'
        )
    record_id = fields.Integer(
        string='ID Path (Model)',
        help="ID of rewrite model"
        )

    @api.model
    def create(self, vals):
        redirectObjs = self.search([
            ('url_from', '=', vals.get('url_from')),
            ('url_to','=', vals.get('url_to')),
            ('record_id','=', vals.get('record_id')),
            ('rewrite_val','=', vals.get('rewrite_val'))
        ])
        if redirectObjs:
            return redirectObjs[0]
        res = super(WebsiteRedirect, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        redirectObjs = []
        if 'url_from' in vals and 'url_to' in vals:
            redirectObjs = self.search([
                ('url_from', '=', vals.get('url_from')),
                ('url_to','=', vals.get('url_to')),
                ('record_id','=', self.record_id),
                ('rewrite_val','=', self.rewrite_val)
            ])
        elif 'url_to' in vals:
            redirectObjs = self.search([
                ('url_to','=', vals.get('url_to')),
                ('url_from','=', self.url_from),
                ('record_id','=', self.record_id),
                ('rewrite_val','=', self.rewrite_val)
            ])
        elif 'url_from' in vals:
            redirectObjs = self.search([
                ('url_from','=', vals.get('url_from')),
                ('url_to','=', self.url_to),
                ('record_id','=', self.record_id),
                ('rewrite_val','=', self.rewrite_val)
            ])
        if redirectObjs:
            return True
        res = super(WebsiteRedirect, self).write(vals)
        return res

    def getUrlSuffix(self, value):
        modelname = value._name
        suffix = self.getSuffix(modelname)
        return suffix

    def trackSuffix(self, modelName):
        website_id = request.env['website'].get_current_website()
        use_suffix = website_id.use_suffix
        suffix = request.env['website.redirect'].sudo().getSuffix(modelName)
        return {'use_suffix':use_suffix, 'suffix':suffix}

    def getSuffix(self, modelname):
        suffix = ''
        website_id = request.env['website'].get_current_website()
        if modelname == 'product.public.category':
            suffix = website_id.suffix_category
        if modelname == 'product.template':
            suffix = website_id.suffix_product
        return suffix

    def unsetUrlSuffix(self, value):
        website_id = request.env['website'].get_current_website()
        suffix = website_id.suffix_category
        if suffix:
            value = value.replace(suffix, '')
        suffix = website_id.suffix_product
        if suffix:
            value = value.replace(suffix, '')
        return value

    def setRewriteUrl(self, data):
        url_from = "/" + data.get('url_from')
        url_to = "/" + data.get('url_to')
        redirectExistObjs = self.search([
            ('url_to','=', url_from),
            ('record_id', '=', data.get('record_id')),
            ('rewrite_val', '=', data.get('rewrite_val'))
        ])
        for redirectExistObj in redirectExistObjs:
            if redirectExistObj.url_to != url_to:
                redirectExistObj.url_to = url_to
        redirectObjs = self.search([('url_from', '=', url_from), ('url_to','=', url_to)])
        if not redirectObjs:
            # data['website_id'] = self.env['website'].get_current_website().id
            data['type'] = '301'
            data['create_type'] = 'system'
            data['url_from'] = url_from
            data['url_to'] = url_to
            data['name'] = url_to
            redirectObjs = self.create(data)
        return redirectObjs

    def getSlugUrlKeyModel(self, value, model):
        res = request.env['product.public.category'].sudo().search([('url_key', '=', value)])
        if not res:
            res = request.env['product.template'].sudo().search([('url_key', '=', value)])
        if res:
            model = res._name
        return model

    def getCategoryUrl(self, categoryObj):
        catUrl = ''
        path = request.httprequest.path
        request.httprequest.path = '/'
        while categoryObj.parent_id:
            categoryObj = categoryObj.parent_id
            urlKey = categoryObj.url_key
            catUrl = urlKey + "/" + catUrl
        return catUrl

    def createUrlKey(self, modelObj, fieldsList):
        url_key = []
        for field in fieldsList:
            if hasattr(modelObj, field):
                name = getattr(modelObj, field)
                name = slugify(name or '').strip().strip('-')
                url_key.append(name)
        urlKey = '-'.join(url_key)
        if not urlKey:
            urlKey = slug(modelObj)
        return urlKey

    def getFieldList(self, pattern, model):
        website_id = model.website_id or self.env['website'].get_current_website()
        modelPattern = website_id.mapped(pattern)[0]
        fieldsList = []
        if modelPattern:
            fieldsList = modelPattern.split(',')
        return fieldsList

    def createRedirectForRewrite(self, vals, modelObj, modelName, pattern):
        if 'url_key' in vals:
            vals['url_key'] = re.sub('[^A-Za-z0-9]+', '-', vals['url_key'])
            oldUrl = modelObj.url_key
            if oldUrl in ['', False, None]:
                oldUrl = slug(modelObj)
            urlTo = vals.get('url_key')
            if urlTo in ['', False, None]:
                fieldsList = self.getFieldList(pattern, modelObj)
                urlKey = self.createUrlKey(modelObj, fieldsList)
                urlTo = urlKey
                vals['url_key'] = urlTo
            if urlTo == oldUrl:
                oldUrl = slug(modelObj)
            redirectData = {
                'rewrite_val':modelName,
                'record_id':modelObj.id,
                'url_from':oldUrl,
                'url_to':urlTo
            }
            self.setRewriteUrl(redirectData)
        return vals

    def setSeoUrlKey(self, pattern, modelObjs):
        failedIds = []
        for modelObj in modelObjs:
            fieldsList = self.getFieldList(pattern, modelObj)
            urlKey = self.createUrlKey(modelObj, fieldsList)
            try:
                modelObj.url_key = urlKey
            except ValidationError as e:
                modelObj.url_key = ''
                if modelObj._name == 'product.template':
                    failedIds.append(modelObj.default_code or '')
            finally:
                pass
        return failedIds

    def get_parent_category(self, hrefUrl=''):
        frontEndLang = request.httprequest.cookies.get('frontend_lang')
        website_id = request.env['website'].get_current_website()
        useCategoryUrl = website_id.use_category_url
        website_id = request.env['website'].get_current_website()
        useServerRewrites = website_id.use_server_rewrites
        if not useCategoryUrl:
            return {"mainCat":False, "use_server_rewrites":useServerRewrites}
        redirectObj = request.env['website.redirect'].sudo()
        categoryUrlKey = redirectObj.unsetUrlSuffix(hrefUrl)
        categoryUrlKey = ''.join(categoryUrlKey.split('/')[-1:])
        categoryObj = request.env['product.public.category'].sudo().search([('url_key', '=', categoryUrlKey)], limit=1)
        catUrl = ''
        if categoryObj:
            catUrl = categoryObj.url_key
            while categoryObj.parent_id:
                categoryObj = categoryObj.parent_id
                urlKey = categoryObj.url_key
                catUrl = urlKey + "/" + catUrl
        if catUrl == '':
            catUrl = False
        return {"mainCat":catUrl, "use_server_rewrites":useServerRewrites, 'lang':frontEndLang}

class Website(models.Model):
    _inherit = "website"

    use_suffix = fields.Boolean(string="Use Suffix in URL", default=True)
    suffix_product = fields.Char(string="Suffix in Product URL", default=".html")
    suffix_category = fields.Char(string="Suffix in Category URL", default=".html")
    pattern_product = fields.Char(string="Pattern for Product URL Key", default="id,name")
    pattern_category = fields.Char(string="Pattern for Category URL Key", default="id,name")
    use_category_url = fields.Boolean(string="Use Category URL on Product", help="""Enable to append category along with product URL in Website""", default=True)
    use_category_hierarchy = fields.Boolean(string="Use Category hierarchy", help="""Enable to manage category hierarchy option in Website""", default=True)
    use_server_rewrites = fields.Boolean(
            string="Use Web Server Rewrites",
            help="""
            By enabling this feature page key will remove from url
            For Example :
            '/shop/product/catalog-product' => '/catalog-product'
            '/blog/my-blog/post/my-blog-first-post' => '/my-blog-first-post'
            """,
            default=True
        )

    @api.multi
    def enumerate_pages(self, query_string=None, force=False):
        res = super(Website, self).enumerate_pages(query_string, force)
        useServerRewrites = self.use_server_rewrites
        for rec in res:
            if 'loc' in rec:
                if useServerRewrites:
                    rec['loc'] = rec['loc'].replace("/shop/product", "").replace("/shop/category", "")
                yield rec
