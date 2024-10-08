# Copyright 2015 Antiun Ingeniería, S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class RequireLoginToCheckout(WebsiteSale):
    @http.route(auth="user")
    def checkout(self, **post):
        response = super().checkout(**post)
        order = request.website.sale_get_order()
        if order is not None and order.original_team_id is not None:
            order.team_id = order.original_team_id
        return response
