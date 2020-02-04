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
  "name"                 :  "Odoo Dynamic Bank Cheque Print",
  "summary"              :  "The module allows you to add various fields to the cheque template in Odoo, so you can print the cheque from Odoo.",
  "category"             :  "Accounting",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Dynamic-Bank-Cheque-Print.html",
  "description"          :  """Odoo Dynamic Bank Cheque Print
Print cheque from bank in Odoo
Print bank check in Odoo
bank check print
Odoo Bank cheque printing
Print payment check
Digital Check writing in Odoo
Odoo Partner cheque print""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_cheque_management",
  "depends"              :  [
                             'account',
                             'website',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'data/cheque_attribute_data.xml',
                             'wizard/invoice_print_cheque_transient_views.xml',
                             'views/account_invoice_inherit_view.xml',
                             'views/bank_cheque_views.xml',
                             'views/website_template_view.xml',
                             'views/cheque_report.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}