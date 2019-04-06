from odoo.tests import common
import  logging
_logger = logging.getLogger(__name__)
class TestProject(common.TransactionCase):
    at_install = True
    post_install = True
    at_update = True

    def test_count(self):
        expected_value = 10
        actual_value = 12

        self.assertTrue(expected_value, actual_value)

        print('Test Case Successful')
        _logger.warn('Your test case is running')