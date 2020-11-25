# -*- coding: utf-8 -*-
import base64
import werkzeug.wrappers
import os
from addons.auth_signup.controllers.main import AuthSignupHome

from odoo import fields, http, modules, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import binary_content
from odoo.addons.portal.controllers.web import Home
from odoo.addons.http_routing.models.ir_http import slug, _guess_mimetype

class Website_Resource(http.Controller):
    @http.route('/resource', type='http', auth="public", website=True)
    def home(self, **kw):
        video = request.env['resource.webresource'].sudo().search(
            [('is_active', '=', True)])
        values = {'videos': video}
        return request.render('res_website.resouces_page_template', {
            'teachers': ["Diana Padilla", "Jody Caroll  aa", "Lester Vaughn"],
            'video': video
        })