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
  "name"                 :  "View Records In New Tab",
  "summary"              :  """View Records In New Tab.""",
  "category"             :  "Website",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "LGPL-3",
  "website"              :  "https://store.webkul.com/Odoo-View-Records-In-New-Tab.html",
  "description"          :  """View Records In New Tab""",
  "live_test_url"        :  "",
  "depends"              :  ['web'],
  # "data"                 :  ['views/template.xml'], AHUJA MIGRATION
  "images"               :  ['static/description/Banner.gif'],
  "application"          :  True,
  "installable"          :  True,
  "assets"              :  {
    "web.assets_backend" :  [
      'odoo_new_tab/static/src/js/list_view.js'
    ]
  },
  "auto_install"         :  False,
  "price"                :  10,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
