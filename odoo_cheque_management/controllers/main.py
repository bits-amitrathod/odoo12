# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

# 2 :  imports of odoo
import odoo
from odoo import http, tools, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class BankChequeManagement(http.Controller):

    @http.route('/bank/cheque/<model("res.bank"):bank_cheque_id>', type='http', auth="user", website=True)
    def bank_cheque_management(self, bank_cheque_id, **post):
        values = {"bank_cheque_obj": bank_cheque_id}
        return request.render("odoo_cheque_management.bank_cheque_management_template", values)

    @http.route('/bank/cheque/update', type='http', auth="user", website=True)
    def bank_cheque_update_attrs(self, **post):
        is_updated = False
        if post.get("cheque_attribute_line_id"):
            is_updated = request.env["bank.cheque.attribute.line"].browse(
                int(post.get('cheque_attribute_line_id'))).write({
                    "top_displacement": int(post.get("y1", 0)),
                    "left_displacement": int(post.get("x1")) if post.get("x1") else 0,
                    "height": int(post.get("h")) if post.get("h") else 0,
                    "width": int(post.get("w")) if post.get("w") else 0,
                    # "font_size": post.get(""),
                    # "font_family": post.get(""),
                })
        values = {
            "bank_cheque_obj": request.env["res.bank"].browse(
            int(post.get('bank_cheque_id'))) if post.get('bank_cheque_id') else False,
            }
        if is_updated:
            values.update({"updated_cheque_attribute_line_id": int(post.get('cheque_attribute_line_id'))})
        # return self.bank_cheque_management(
        #     bank_cheque_id=values.get("bank_cheque_obj"))
        # post = {}
        # return request.render("odoo_cheque_management.bank_cheque_management_template", values)
        return request.redirect("/bank/cheque/%s" % slug(values.get("bank_cheque_obj")))

    @http.route('/bank/cheque/preview/<model("res.bank"):bank_cheque_id>', type='http', auth="user", website=True)
    def bank_cheque_preview(self, bank_cheque_id, **post):
        values = {"bank_cheque_obj": bank_cheque_id}
        return request.render("odoo_cheque_management.bank_cheque_priview", values)
