# -*- coding: utf-8 -*-
from odoo import http

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import json
from odoo.http import Controller, request, route


class VendorOfferAutomation(http.Controller):

    @http.route('/offer_template_import/set_file', methods=['POST'])
    def set_file(self, file, import_id, jsonp='callback'):
        import_id = int(import_id)

        written = request.env['sps.vendor.offer.template.transient'].browse(import_id).sudo().write({
            'file': file.read(),
            'file_name': file.filename,
            'file_type': file.content_type,
        })

        return 'window.top.%s(%s)' % (misc.html_escape(jsonp), json.dumps({'result': written}))
