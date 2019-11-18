# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo.addons.http_routing.models.ir_http import slug as httpslug

from odoo.addons.http_routing.models import ir_http as httpRoutingObj
from odoo.addons.http_routing.models.ir_http import ModelConverter, RequestUID, unslug_url
from odoo import api, fields, models, _
import odoo
import werkzeug
from odoo.http import request
import re
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)

def slug(value):
    field = 'url_key'
    if field and isinstance(value, models.BaseModel) and hasattr(value, field):
        name = getattr(value, field)
        if name:
            suffix = getSuffix(value)
            if suffix:
                name = "{}{}".format(name, suffix)
            return name
    if not value:
        raise request.not_found()
    superslug = httpslug(value)
    return superslug

httpRoutingObj.slug = slug

def getSuffix(value):
    suffix = ''
    use_suffix = request.website.use_suffix
    if use_suffix:
        suffix = request.env['website.redirect'].sudo().getUrlSuffix(value)
    return suffix

class ModelConverterRewrite(ModelConverter):

    def __init__(self, url_map, model=False, domain='[]'):
        super(ModelConverter, self).__init__(url_map, model)
        self.domain = domain
        self.regex = r'(?:(\w{1,2}|\w[A-Za-z0-9-._]+?))(?=$|/)'

    def generate(self, uid, dom=None, args=None):
        Model = request.env[self.model].sudo(uid)
        # Allow to current_website_id directly in route domain
        args.update(current_website_id=request.env['website'].get_current_website().id)
        domain = safe_eval(self.domain, (args or {}).copy())
        if dom:
            domain += dom
        for record in Model.search_read(domain=domain, fields=['write_date', Model._rec_name]):
            if record.get(Model._rec_name, False):
                yield {'loc': (record['id'], record[Model._rec_name])}

    def to_url(self, value):
        req_page = request.httprequest.path
        if req_page == '/sitemap.xml':
            if len(value) > 1:
                value = request.env[self.model].browse(value[0])
        try:
            name = slug(value)
        except AccessError:
            name = ''
        return name

    def to_python(self, value):
        record_id = None
        value = self.unsetSuffix(value)

        modelObj = self.getUrlKeyModel(value)
        self.model = modelObj
        _uid = RequestUID(value=value, converter=self)
        env = api.Environment(request.cr, _uid, request.context)
        field = 'url_key'
        if field and field in env[self.model]._fields:
            res = env[self.model].sudo().search([(field, '=', value)])
            if res:
                record_id = res[0].id
        if not record_id:
            customRegex = r'(?:(\w{1,2}|\w[A-Za-z0-9-_]+?\w)-)?(-?\d+)(?=$|/)'
            matching = re.match(customRegex, value)
            if matching:
                record_id = int(matching.group(2))
        if not record_id:
            return None
        if record_id < 0:
            if not env[self.model].browse(record_id).exists():
                record_id = abs(record_id)
        return env[self.model].browse(record_id)

    def getUrlKeyModel(self, value):
        model = self.model
        searchKey = "/"+value
        redirectObj = request.env['website.redirect'].sudo()
        res = redirectObj.search([('url_to', '=', searchKey)], 0, 1, 'id desc')
        if not res:
            modelName = redirectObj.getSlugUrlKeyModel(value, model)
            if modelName:
                model = modelName
        if res:
            if res.rewrite_val != 'custom':
                model = res.rewrite_val
        return model

    def unsetSuffix(self, value):
        value = request.env['website.redirect'].sudo().unsetUrlSuffix(value)
        return value

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_converters(cls):
        return dict(
            super(IrHttp, cls)._get_converters(),
            model=ModelConverterRewrite,
        )

    @classmethod
    def _dispatch(cls):
        if not hasattr(request, "jsonrequest") and not hasattr(request, 'rerouting'):
            req_page = request.httprequest.path
            if "/web/database/" in req_page:
                return super(IrHttp, cls)._dispatch()
            redirectObj = request.env['website.redirect'].sudo()
            if '/web/image' not in req_page and '/web/content' not in req_page:
                try:
                    page = ''
                    if 'page' in req_page:
                        page = "/".join(req_page.split('/')[-2:])
                        req_page = "/".join(req_page.split("page")[:-1])[:-1]
                    redirect = cls._serve_url_redirect(req_page, redirectObj)
                    if redirect:
                        suffix = redirectObj.getSuffix(redirect.rewrite_val)
                        url_to = redirect.url_to
                        if page:
                            url_to = url_to + "/" + page
                        if suffix:
                            url_to = "{}{}".format(url_to, suffix)
                        return werkzeug.utils.redirect(url_to, redirect.type)
                    else:
                        website_id = request.env['website'].get_current_website()
                        useServerRewrites = website_id.use_server_rewrites
                        if '/shop/product' not in req_page and '/shop/category' not in req_page:
                            if useServerRewrites:
                                actualUrl = req_page
                                redirect = cls._serve_url_to_redirect(req_page, redirectObj)
                                if redirect:
                                    checkSuffix = cls._check_for_suffix(redirectObj, redirect, actualUrl)
                                    if checkSuffix:
                                        return werkzeug.utils.redirect(checkSuffix, '302')
                                    frontEndLang = request.httprequest.cookies.get('frontend_lang')
                                    rewrite_val = redirect.rewrite_val
                                    defaultLang = request.lang
                                    defaultLangObj = request.env['ir.http']._get_default_lang()
                                    if defaultLangObj:
                                        defaultLang = defaultLangObj.code
                                    if rewrite_val == 'product.template':
                                        urlKey = '/'.join(req_page.split('/')[-1:])
                                        if frontEndLang != defaultLang:
                                            if frontEndLang:
                                                redirectUrl = "/{}/shop/product/{}".format(frontEndLang, urlKey)
                                            else:
                                                redirectUrl = "/shop/product/" + urlKey
                                        else:
                                            redirectUrl = "/shop/product/" + urlKey
                                        return cls.reroute(redirectUrl)
                                    if rewrite_val == 'product.public.category':
                                        urlKey = '/'.join(req_page.split('/')[-1:])
                                        if frontEndLang != defaultLang:
                                            if frontEndLang:
                                                redirectUrl = "/{}/shop/category/{}".format(frontEndLang, urlKey)
                                            else:
                                                redirectUrl = "/shop/category/" + urlKey
                                        else:
                                            redirectUrl = "/shop/category/" + urlKey
                                        if page:
                                            redirectUrl = redirectUrl + "/" + page
                                        return cls.reroute(redirectUrl)
                except Exception as e:
                    _logger.info("^^^^^^^^^^^^Exception^^^^^^^^^^^^^^^^: %r", e)
                    pass
        res = super(IrHttp, cls)._dispatch()
        try:
            website_id = request.env['website'].get_current_website()
            useServerRewrites = website_id.use_server_rewrites
            if res and res.get_data() and useServerRewrites:
                resData = res.get_data()
                # if b"href='/shop/product/" in resData or b"href='/shop/category/" in resData or b'href="/shop/product/' in resData or b'href="/shop/category/' in resData:
                currentPage = request.httprequest.environ.get('PATH_INFO')
                currentPage = currentPage.replace("/shop/product/", "/").replace("/shop/category/", "/")
                redirectObj = request.env['website.redirect'].sudo().get_parent_category(currentPage)
                mainCat = redirectObj.get('mainCat')
                use_server_rewrites = redirectObj.get('use_server_rewrites')
                lang = redirectObj.get('lang')
                dataString = resData.decode("utf-8")
                if mainCat:
                    replaceUrl = "/shop/product/{}/".format(mainCat)
                    dataString = dataString.replace("/shop/product/", replaceUrl)
                if lang:
                    replaceLangProUrl = "/{}/shop/product/".format(lang)
                    replaceLangCatUrl = "/{}/shop/category/".format(lang)
                    dataString = dataString.replace(replaceLangProUrl, "/shop/product/").replace(replaceLangCatUrl, "/shop/category/")
                if use_server_rewrites:
                    dataString = dataString.replace("/shop/product/", "/").replace("/shop/category/", "/")
                res.set_data(dataString.encode("utf-8"))
        except Exception as e:
            pass
        return res

    @classmethod
    def _serve_url_redirect(cls, req_page, redirectObj):
        req_page = redirectObj.unsetUrlSuffix(req_page)
        urlKey = ''.join(req_page.split('/')[-1:])
        if not urlKey:
            if req_page[-1:] == '/':
                urlKey = req_page.replace('/', '')
        domain = [('url_from', '=', req_page)]
        if urlKey:
            urlKey = "/" + urlKey
            domain = ['|', ('url_from', '=', req_page),('url_from', '=', urlKey)]
        redirectObjs = redirectObj.search(domain, limit=1)
        if redirectObjs:
            if redirectObjs.url_to == req_page:
                return False
        return redirectObjs

    @classmethod
    def _serve_url_to_redirect(cls, req_page, redirectObj):
        try:
            req_page = redirectObj.unsetUrlSuffix(req_page)
            urlKey = ''.join(req_page.split('/')[-1:])
            if not urlKey:
                if req_page[-1:] == '/':
                    urlKey = req_page.replace('/', '')
            domain = [('url_to', '=', req_page)]
            transDomain = ['|', ('value', '=', req_page.replace('/', '')),('value', '=', urlKey)]
            if urlKey:
                urlKey = "/" + urlKey
                domain = ['|', ('url_to', '=', req_page),('url_to', '=', urlKey)]
            redirectObjs = redirectObj.search(domain, limit=1)
            if not redirectObjs:
                resObjs = request.env['ir.translation'].sudo().search(transDomain)
                if resObjs:
                    urlKey = "/" + resObjs.source
                    domain = [('url_to', '=', urlKey)]
                    redirectObjs = redirectObj.search(domain, limit=1)
        except Exception as e:
            _logger.info("------Exception--_serve_url_to_redirect----- : %r", e)
        return redirectObjs

    @classmethod
    def _check_for_suffix(cls, redirectObj, redirectObjs, actualUrl):
        suffixData = redirectObj.trackSuffix(redirectObjs.rewrite_val)
        seoSuffix = suffixData.get('suffix')
        if suffixData.get('use_suffix') and seoSuffix:
            if seoSuffix not in actualUrl:
                actualUrl = "{}{}".format(actualUrl, seoSuffix)
                return actualUrl
        else:
            if seoSuffix and seoSuffix in actualUrl:
                actualUrl = actualUrl.replace(seoSuffix, '')
                return actualUrl
        return False

class IrUiView(models.Model):
    _inherit = ["ir.ui.view"]

    @api.model
    def _prepare_qcontext(self):
        qcontext = super(IrUiView, self)._prepare_qcontext()
        qcontext['slug'] = slug
        qcontext['unslug_url'] = unslug_url
        return qcontext
