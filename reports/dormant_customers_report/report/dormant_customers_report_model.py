import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.dormant_customers_report.dorm_cust_report_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['res.partner'].browse(docids)
        return {
            'data': records}
