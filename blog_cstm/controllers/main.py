# -*- coding: utf-8 -*-
import odoo
from odoo import fields, http
from odoo.http import request
from odoo.addons.website_blog.controllers.main import WebsiteBlog
# from odoo.addons.http_routing.models.ir_http import slug, unslug

class WebsiteBlog(WebsiteBlog):

    def blog_post(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):
        response = super(WebsiteBlog, self).blog_post(blog, blog_post, tag_id, page, enable_editor, **post)
        payload = response.qcontext
        popular = request.env['blog.post'].search([('website_published', '=', True),('id','!=',blog_post.id)], limit=3, order ='visits DESC')
        payload['author_info'] = payload['blog_post'].author_id
        payload['popular_post'] = popular
        response = request.render("website_blog.blog_post_complete", payload)
        return response


    def blog(self, blog=None, tag=None, page=1, search=None, **opt):
        response = super(WebsiteBlog, self).blog(blog, tag, page, search, **opt)
        payload = response.qcontext
        # sep = '-'
        # if tag:
        #     tag_id = int(tag.split(sep, 1)[1])
        #     tag_name=request.env['blog.tag'].search([('id', '=',tag_id)],limit=1)
        #     payload['tag_name'] = tag_name
        response = request.render("website_blog.blog_post_short", payload)
        return response

