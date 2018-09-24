
from odoo import api, models
import logging

log = logging.getLogger(__name__)

class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.sr_sales_report_compmonth.salesbymonth_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': data['form'],
            'current_start_date': data['current_start_date'],
            'current_end_date': data['current_end_date'],
            'last_start_date': data['last_start_date'],
            'last_end_date': data['last_end_date'],
        }
