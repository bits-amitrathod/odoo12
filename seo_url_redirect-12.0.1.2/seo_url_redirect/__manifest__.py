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
  "name"                 :  "SEO-URL Redirect/Rewrite",
  "summary"              :  "SEO-URL Redirect/Rewrite module helps to redirect or redirect a URL to another URL to avoid page not found error.",
  "category"             :  "Website",
  "version"              :  "1.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-SEO-URL-Redirect-Rewrite.html",
  "description"          :  """SEO
                            Search Engine Optimization
                            URL
                            SEO URL
                            Redirect/Rewrite
                            Rewrite
                            Redirect
                            SEO-URL Redirect/Rewrite
                            Odoo SEO-URL Redirect/Rewrite
                            URL Redirect/Rewrite
                            URL Rewrite
                            URL Redirect
                            """,
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=seo_url_redirect",
  "depends"              :  [
                             'website_sale',
                             'website_webkul_addons',
                             'wk_wizard_messages',
                            ],
  "data"                 :  [
                             'views/templates.xml',
                             'views/product_template_views.xml',
                             'views/product_views.xml',
                             'views/rewrite_view.xml',
                             'data/data_seo.xml',
                             'data/seo_server_actions.xml',
                             'views/website_views.xml',
                             'views/rewrite_menu.xml',
                             'views/res_config_views.xml',
                             'views/webkul_addons_config_inherit_view.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
  "post_init_hook"       :  "_update_seo_url",
}
