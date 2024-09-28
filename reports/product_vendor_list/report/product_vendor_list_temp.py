
import logging
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

log = logging.getLogger(__name__)

class ReportProductVendorList(models.AbstractModel):
    _name = 'report.product_vendor_list.productvendorlist_temp_test'
    _description = "Report Product Vendor List"


    def _get_report_values(self, docids, data=None):
         return {'data': list(self.env['purchase.order.line'].browse(docids))}