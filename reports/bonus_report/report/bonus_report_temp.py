import logging
from odoo import api, fields, models
from odoo.tools import float_repr
import datetime

log = logging.getLogger(__name__)


class Discount():
    sale_order = ''
    customer = ''
    confirmation_date = 0
    amount = 0
    discount_amount = 0
    total_amount = 0


class ReportProductVendorList(models.AbstractModel):
    _name = 'report.bonus_report.bonusreport_temp_test'
    @api.model
    def get_report_values(self, docids, data=None):
         return {'data': self.env['purchase.order'].browse(docids)}