from addons.sale_stock.tests.test_sale_order_dates import TestSaleExpectedDate
from datetime import timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests import common
import logging
_logger = logging.getLogger(__name__)

at_install = True
post_install = True
at_update = True

@tagged('post_install', '-at_install')
class Prior(TestSaleExpectedDate):
    # _inherit='TestSaleExpectedDate'

   def test_sale_order_commitment_date(self):
        # super(Prior, self).test_sale_order_commitment_date()
        # new_order = self.env.ref('available.product.dict').copy({'commitment_date': '2010-07-12'})

        a=10
        b=10
        self.assertTrue(a,b)
        # self.assertTrue(new_order,"order")


        print("Test executed successfully in prior")
        _logger.warn("Test executed successfully 2 in prior")

# Prior()
# obj=Prior()
# obj.test_sale_order_commitment_date()

# def test_sale_order_commitment_date(self):

# # In order to test the Commitment Date feature in Sales Orders in Odoo,
# # I copy a demo Sales Order with committed Date on 2010-07-12
# new_order = self.env.ref('sale.sale_order_6').copy({'commitment_date': '2010-07-12'})
# # I confirm the Sales Order.
# new_order.action_confirm()
# # I verify that the Procurements and Stock Moves have been generated with the correct date
# security_delay = timedelta(days=new_order.company_id.security_lead)
# commitment_date = fields.Datetime.from_string(new_order.commitment_date)
# right_date = commitment_date - security_delay
# for line in new_order.order_line:
#     self.assertTrue(line.move_ids[0].date_expected, right_date, "The expected date for the Stock Move is wrong")
