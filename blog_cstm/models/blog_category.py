# -*- coding: utf-8 -*-

import re
from odoo.tools import image
from odoo import _, api, fields, models
from odoo.tools.translate import html_translate

class BlogPostCategory(models.Model):
    _name = 'blog.post.category'
    _description = 'Blog Post category'
    name = fields.Char('Name', required=True)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _default_content(self):
        return '''  
                   <p>Omni berest officiate secea nume vellabori con nos experum ex et dolupta temqui idem quis ipiento tet alitatem quae nos dolent.</p>
				<p>Untuscid ut fuga. Ducimintia nat ut quissi il iderfer umquamendam adi netur reicips andita sapit,
                                                    nost, que et velendi tatinus si nimus esequam, sed mi, ut omnis aut reicil in resendendem. Adiat
                                                    quatum et ped evenienitate quiam et quam nitatem rem facerum fugita que nobistorem velibus, to
                                                    dolorit mi, officae nonem sum nobit ex etur?Omni berest officiate secea nume vellabori con nos
                                                    experum ex et dolupta temqui idem quis ipiento tet alitatem quae nos dolent.</p>
				<p>Untuscid ut fuga. Ducimintia nat ut quissi il iderfer umquamendam adi netur reicips andita sapit,
                                
        '''

    def _default_html(self):
        return '''  
                 <img src="/sps_theme/static/src/images/blog.png" class="img-fluid"/>     
            '''

    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False)
    title_img = fields.Html('Content', default=_default_html, translate=html_translate, sanitize=False)
    image = fields.Image('Image', store=True)
    image_medium = fields.Binary('Medium', store=True, attachment=True)
    image_thumb = fields.Binary('Thumbnail',  store=True, attachment=True)

    def description_content(self):
        s3 =''
        data = self.content
        if data !='':
            s3 = re.sub("[\<\[].*?[\>\]]", "", re.search('>(.*)', re.search('<p(.*)</p>',data).group(1)).group(1))
            if 14 < len(s3.split()):
                s3 =" ".join((s3.split()[:14]))
                s3 = s3 + ' ...'


        return s3