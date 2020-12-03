# -*- coding: utf-8 -*-

import pytz

from odoo import _, api, fields, models
from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

from dateutil.relativedelta import relativedelta


class BlogPostCategory(models.Model):
    _name = 'blog.post.category'
    _description = 'Blog Post category'
    name = fields.Char('Name', required=True)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _default_content(self):
        return '''
            <section class="s_text_block">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-12 mb16 mt16">
                            <p class="o_default_snippet_text">''' + _("sps Theme CSTM") + '''</p>
                        </div>
                    </div>
                </div>
            </section>
        '''

    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)