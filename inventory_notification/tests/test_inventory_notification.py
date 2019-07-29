from odoo.addons.base.tests.test_reports import TestReports
from odoo.tests import tagged

import odoo
import odoo.tests

@odoo.tests.tagged('post_install', '-at_install')
class TestReports(odoo.tests.TransactionCase):
    print("Inside Child 1")
    def test_reports(self):
        print("Inside Child")

        # super(Inventory_Notification_Test, self).test_reports()

        # self.a=10
        # self.b=10
        # self.assertTrue(self.a,self.b)
        print("Inventory Notification Test case executed successfully $$$")
