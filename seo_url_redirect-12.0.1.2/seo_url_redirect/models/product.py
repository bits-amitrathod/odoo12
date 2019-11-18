# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models, _

class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    url_key = fields.Char(
        string='SEO Url Key',
        default='', translate=True,
        help="SEO Url Key for Product Category")

    @api.multi
    def __check_url_key_uniq(self):
        for obj in self:
            if obj.url_key:
                urlKey = "/" + obj.url_key
                res = self.env['website.redirect'].sudo().search([('url_to', '=', urlKey), ('rewrite_val', '!=', 'custom')], 0, 2, 'id desc')
                if res:
                    for resObj in res:
                        if resObj.record_id == obj.id: 
                            if resObj.rewrite_val != "product.public.category":
                                return False
                        else:
                            return False
        return True

    _constraints = [(__check_url_key_uniq, 'SEO URL Key must be unique!', ['url_key'])]

    @api.model
    def create(self, vals):
        res = super(ProductPublicCategory, self).create(vals)
        if res.url_key in ['', False, None]:
            self.env['website.redirect'].setSeoUrlKey('pattern_category', res)
        return res

    @api.multi
    def write(self, vals):
        for catObj in self:
            vals = self.env['website.redirect'].createRedirectForRewrite(vals, catObj, 'product.public.category', 'pattern_category')
        res = super(ProductPublicCategory, self).write(vals)
        return res

    @api.multi
    def update_seo_url(self):
        categoryIds = self._context.get('active_ids')
        categoryObjs = self.search([('id', 'in', categoryIds)])
        self.env['website.redirect'].setSeoUrlKey('pattern_category', categoryObjs)
        text = "SEO Url key of {} category(s) have been successfully updated.".format(len(categoryObjs))
        return self.env['wk.wizard.message'].genrated_message(text)