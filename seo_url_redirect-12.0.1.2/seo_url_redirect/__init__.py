#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
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

from . import models
from odoo import api, SUPERUSER_ID
from odoo.addons.http_routing.models.ir_http import slug

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='12.0':raise Warning('Module support Odoo series 12.0 found {}.'.format(server_serie))

def _update_seo_url(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        categoryObjs = env['product.public.category'].search([])
        env['website.redirect'].setSeoUrlKey('pattern_category', categoryObjs)
        templateObjs = env['product.template'].search([])
        env['website.redirect'].setSeoUrlKey('pattern_product', templateObjs)
    except Exception as e:
        pass
