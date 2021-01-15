# -*- coding: utf-8 -*-

import pytz
import requests
from PIL import Image

import base64
import datetime
import io
import json
import re
from odoo.tools import image
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
                   

                                    <div class="banner-wrapper py-3">
                                        <img src="/sps_theme/static/src/images/blog.png" class="img-fluid"/>
                                    </div>
                                    <div class="text-left py-3">
                                        <h1  class="about-header ft-32"> Choose to save money without sacrificing quality of care </h1>
                                     </div>
                                    <div class="blog-detail">
                                        <div class="d-flex">
                                            <div class="profile-img-wrapper align-self-center">
                                                <div class="profile-img">
                                                     <img src="/sps_theme/static/src/images/profile.png" class="img-fluid"/>
                                                </div>
                                            </div>

                                            <div class="user-info section-description">
                                                <p class="lh-25"><span class="medium-font">Joan Grayson</span> in <span class="medium-font">News</span></p>
                                                <p  class="lh-25">Jun 14 • 3 min read</p>
                                            </div>
                                        </div>
                                            <div class="section-description mt-4">
                                                <p>Omni berest officiate secea nume vellabori con nos experum ex et dolupta temqui idem quis
                                                    ipiento tet alitatem quae nos dolent.
                                                </p>
                                                <p>Untuscid ut fuga. Ducimintia nat ut quissi il iderfer umquamendam adi netur reicips andita sapit,
                                                    nost, que et velendi tatinus si nimus esequam, sed mi, ut omnis aut reicil in resendendem. Adiat
                                                    quatum et ped evenienitate quiam et quam nitatem rem facerum fugita que nobistorem velibus, to
                                                    dolorit mi, officae nonem sum nobit ex etur?Omni berest officiate secea nume vellabori con nos
                                                    experum ex et dolupta temqui idem quis ipiento tet alitatem quae nos dolent.</p>
                                                <p>Untuscid ut fuga. Ducimintia nat ut quissi il iderfer umquamendam adi netur reicips andita sapit,
                                                nost, que et velendi tatinus si nimus esequam, sed mi, ut omnis aut reicil in resendendem. Adiat
                                                quatum et ped evenienitate quiami tatinus si nimus esequam, sed mi, ut omnis aut reicil in
                                                resendendem. Adiat quatum et ped evenienitate quiam et quam nitatem rem facerum fugita que
                                                nobistorem velibus, to dolorit mi, officae nonem sum i tatinus si nimus esequam, sed mi, ut omnis
                                                aut reicil in resendendem. Adiat quatum et ped evenienitate quiam et quam nitatem rem facerum
                                                fugita que nobistorem velibus, to dolorit mi, officae nonem sum</p>
                                            </div>
                                    </div>
                                
        '''

    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)
    image = fields.Binary('Image', attachment=True)
    image_medium = fields.Binary('Medium', compute="_get_image", store=True, attachment=True)
    image_thumb = fields.Binary('Thumbnail', compute="_get_image", store=True, attachment=True)

    @api.depends('image')
    def _get_image(self):
        for record in self:
            if record.image:
                record.image_medium = image.crop_image(record.image, type='top', ratio=(4, 3), size=(500, 400))
                record.image_thumb = image.crop_image(record.image, type='top', ratio=(4, 3), size=(200, 200))
            else:
                record.image_medium = False
                record.iamge_thumb = False