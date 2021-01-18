# -*- coding: utf-8 -*-
import odoo
from odoo import fields, http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug

class WebsiteBlog(odoo.addons.website_blog.controllers.main.WebsiteBlog):
    @http.route([
        '''/blog/<model("blog.blog", "[('website_id', 'in', (False, current_website_id))]"):blog>/post/<model("blog.post", "[('blog_id','=',blog[0])]"):blog_post>''',
    ], type='http')
    def blog_post(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):
        response = super(WebsiteBlog, self).blog_post(blog, blog_post, tag_id, page, enable_editor, **post)
        payload = response.qcontext
        popular = request.env['blog.post'].search([('website_published', '=', True),('id','!=',blog_post.id)], limit=3, order ='visits DESC')
        payload['author_info'] = payload['blog_post'].author_id
        payload['popular_post'] = popular
        response = request.render("website_blog.blog_post_complete", payload)
        return response