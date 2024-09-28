# -*- coding: utf-8 -*-
import base64
import odoo
import werkzeug.wrappers
from odoo.addons.website.controllers.main import QueryURL
import json
import werkzeug
from odoo import fields, http, modules, SUPERUSER_ID
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_blog.controllers.main import WebsiteBlog

class Website_Resource(http.Controller):
    @http.route([
        '/resource',
        '/resource/page/<int:page>'
    ], type='http', auth="public", website=True)
    def home(self,page=0, **kw):
        video = request.env['resource.webresource'].sudo().search(
            [('website_published', '=', True), ('category', '=', 'video')])
        limit = 9
        if page == 0:
            offset = 0
        else:
            offset = (page-1) * limit
        edu = request.env['slide.slide'].sudo().search([('website_published', '=', True)])
        educational = []
        for x in edu:
            if x.category_id.name =='Educational':
                educational.append(x)

        aw = request.env['slide.slide'].sudo().search([('website_published', '=', True)])
        # awards = request.env['resource.webresource'].sudo().search(
        #     [('website_published', '=', True), ('category', '=', 'award')])
        awards = []
        for x in aw:
            if x.category_id.name == 'Award':
                awards.append(x)
        total_post = request.env['blog.post'].sudo().search([('website_published', '=', True)])
        blogPost = request.env['blog.post'].sudo().search([('website_published', '=', True)],offset=offset, limit=limit)

        pager = request.website.pager(
            url="/resource",
            url_args={},
            total=len(total_post),
            page=page,
            step=limit
        )

        return request.render('res_website.resouces_page_template', {
            'teachers': ["Diana Padilla", "Jody Caroll  aa", "Lester Vaughn"],
            'video': video,
            'blog_post' : blogPost,
            'educational':educational,
            'awards':awards,
            'pager':pager

        })

class blog_resource(WebsiteBlog):

    @http.route([
        '''/blog/<model("blog.blog"):blog>/<model("blog.post", "[('blog_id','=',blog.id)]"):blog_post>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def blog_posts(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):
        """ Prepare all values to display the blog.
        :return dict values: values for the templates, containing
         - 'blog_post': browse of the current post
         - 'blog': browse of the current blog
         - 'blogs': list of browse records of blogs
         - 'tag': current tag, if tag_id in parameters
         - 'tags': all tags, for tag-based navigation
         - 'pager': a pager on the comments
         - 'nav_list': a dict [year][month] for archives navigation
         - 'next_post': next blog post, to direct the user towards the next interesting post
        """
        if not blog.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()

        BlogPost = request.env['blog.post']
        date_begin, date_end = post.get('date_begin'), post.get('date_end')

        pager_url = "/blogpost/%s" % blog_post.id

        pager = request.website.pager(
            url=pager_url,
            total=len(blog_post.website_message_ids),
            page=page,
            step=self._post_comment_per_page,
            scope=7
        )
        pager_begin = (page - 1) * self._post_comment_per_page
        pager_end = page * self._post_comment_per_page
        comments = blog_post.website_message_ids[pager_begin:pager_end]

        tag = None
        if tag_id:
            tag = request.env['blog.tag'].browse(int(tag_id))
        blog_url = QueryURL('', ['blog', 'tag'], blog=blog_post.blog_id, tag=tag, date_begin=date_begin,
                            date_end=date_end)

        if not blog_post.blog_id.id == blog.id:
            return request.redirect("/blog/%s/post/%s" % (slug(blog_post.blog_id), slug(blog_post)), code=301)

        tags = request.env['blog.tag'].search([])

        # Find next Post
        blog_post_domain = [('blog_id', '=', blog.id)]
        if not request.env.user.has_group('website.group_website_designer'):
            blog_post_domain += [('post_date', '<=', fields.Datetime.now())]

        all_post = BlogPost.search(blog_post_domain)

        if blog_post not in all_post:
            return request.redirect("/blog/%s" % (slug(blog_post.blog_id)))

        # should always return at least the current post
        all_post_ids = all_post.ids
        current_blog_post_index = all_post_ids.index(blog_post.id)
        nb_posts = len(all_post_ids)
        next_post_id = all_post_ids[(current_blog_post_index + 1) % nb_posts] if nb_posts > 1 else None
        next_post = next_post_id and BlogPost.browse(next_post_id) or False

        values = {
            'tags': tags,
            'tag': tag,
            'blog': blog,
            'blog_post': blog_post,
            'blog_post_cover_properties': json.loads(blog_post.cover_properties),
            'main_object': blog_post,
            'nav_list': self.nav_list(blog),
            'enable_editor': enable_editor,
            'next_post': next_post,
            'next_post_cover_properties': json.loads(next_post.cover_properties) if next_post else {},
            'date': date_begin,
            'blog_url': blog_url,
            'pager': pager,
            'comments': comments,
        }
        response = request.render("website_blog.blog_post_complete", values)

        request.session[request.session.sid] = request.session.get(request.session.sid, [])
        if not (blog_post.id in request.session[request.session.sid]):
            request.session[request.session.sid].append(blog_post.id)
            # Increase counter
            blog_post.sudo().write({
                'visits': blog_post.visits + 1,
                'write_date': blog_post.write_date,
            })
        return response
