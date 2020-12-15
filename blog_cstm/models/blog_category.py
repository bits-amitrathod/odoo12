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
                    <section class="blog pt-3 pb-5">
                        <div class="container">
                            <div class="row">
                                <div class="col-12">
                                     <div class="btn-wrapper">
                                        <button class="btn btn-info">Resources Home</button>
                                    </div>
                                </div>
                                <div class="col-md-9">

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
                                </div>
                                <div class="col-md-3">
                                    <div class="popular-post">
                                        <h3 class="side-title">Popular Posts</h3>
                                    </div>
                                    <div class="section-description">
                                        <div class="story-list">
                                            <div class="bulleted-list">
                                                <span>01</span>
                                            </div>
                                            <div class="list-description">
                                                <p class="mb-2 lh-25"><a href="javascript:void(0)"><span class="medium-font">Choose to save money without sacrificing quality of care</span></a></p>
                                                <div class="user-info">
                                                    <p class="f14 mb-0 "><span class="medium-font">Joan Grayson</span> in <span class="medium-font">News</span></p>
                                                    <p  class="f14 mb-0">Jun 14 • 3 min read</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="see-all">
                                            <a class="btn btn-link">
                                               SEE ALL POPULAR  <i class="fa fa-angle-right"></i>
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </section>
        '''

    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)