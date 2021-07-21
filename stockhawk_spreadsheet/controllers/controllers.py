# -*- coding: utf-8 -*-
import odoo
import json
import logging
from odoo import fields, http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class StockhawkSpreadsheet(http.Controller):

    @http.route(['/spreadsheet/stockhawk_spreadsheet'], type='http', auth="public", website=True)
    def stockhawk_spreadsheet(self):
        print('In stockhawk_spreadsheet')
        if request.session.uid:
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            if user and user.partner_id and user.partner_id.id:
                return http.request.render('stockhawk_spreadsheet.stockhawk_spreadsheet_view')
