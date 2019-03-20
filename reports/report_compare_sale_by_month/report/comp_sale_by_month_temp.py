
import logging
from odoo import api, models

log = logging.getLogger(__name__)

class ReportCompareSaleByMonthWise(models.AbstractModel):
    _name = 'report.report_compare_sale_by_month.compsalebymonth_template'

    @api.model
    def get_report_values(self, docids, data=None):
         return {'data': self.env['product.product'].browse(docids)}