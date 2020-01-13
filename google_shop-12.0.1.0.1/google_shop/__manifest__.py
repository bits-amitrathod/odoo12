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
  "name"                 :  " Google Shop",
  "summary"              :  "Google Shop facilitates you to integrate Google Merchant Account with Odoo. It allows you to send the products of Odoo into google shop.",
  "category"             :  "Website",
  "version"              :  "1.1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Mandeep Duggal",
  "website"              :  "https://store.webkul.com/Odoo-Google-Shop.html",
  "description"          :  """Google Merchant Account with Odoo
Odoo Google Shop
Google Shop in Odoo
Google Shop
Google Merchant Center Integration
Google Shopping Ads
Google Shopping Feeds
Google
Google Integration with Odoo
Google Integration""",
  "live_test_url"        :  "https://store.webkul.com/",
  "depends"              :  [
                             'base',
                             'wk_wizard_messages',
                             'website_sale',
                            ],
  "data"                 :  [
                             'security/google_shop_security.xml',
                             'security/ir.model.access.csv',
                             'views/templates.xml',
                             'views/google_shop_view.xml',
                             'views/oauth2_detail_view.xml',
                             'views/google_fields_view.xml',
                             'views/field_mapping_view.xml',
                             'views/product_mapping_view.xml',
                            ],
  "demo"                 :  ['demo/demo.xml'],
  "css"                  :  [],
  "js"                   :  [],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
}
