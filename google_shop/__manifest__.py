# -*- coding: utf-8 -*-
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
{
  "name"                 :  "Google Shopping Feed",
  "summary"              :  """This module allows you to send the products of odoo into google shop.""",
  "category"             :  "eCommerce",
  "version"              :  "1.0.4",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Kunal Chaudhary Rajora",
  "website"              :  "https://store.webkul.com/Odoo-Google-Shop.html",
  "description"          :  """Allows you to send the products of odoo into google shop""",
  "live_test_url"        :  "",
  "depends"              :  [
                             'base',
                             'wk_wizard_messages',
                             'website_sale',
                            ],
  "data"                 :  [
                             'security/google_security.xml',
                             'security/ir.model.access.csv',
                             # 'views/templates.xml',
                             # 'views/google_shop_view.xml',
                             # 'views/oauth2_detail_view.xml',
                             # 'views/google_fields_view.xml',
                             # 'views/field_mapping_view.xml',
                             # 'views/product_mapping_view.xml',
                            ],
  "demo"                 :  ['demo/demo.xml'],
  "css"                  :  [],
  "js"                   :  [],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "USD",
}
