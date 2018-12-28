
import logging
from odoo import api, models
from datetime import datetime

log = logging.getLogger(__name__)

class ReportCompareSaleByMonthWise(models.AbstractModel):
    _name = 'report.report_compare_sale_by_month.compsalebymonth_template'

    @api.model
    def get_report_values(self, docids, data=None):

        popup = self.env['compbysale.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.compute_at_date:
            date = datetime.strptime(popup.last_start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + \
                   datetime.strptime(popup.last_end_date, '%Y-%m-%d').strftime('%m/%d/%Y')+"      "+\
                   datetime.strptime(popup.current_start_date, '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + \
                   datetime.strptime(popup.current_end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'data': self.env['product.product'].browse(docids), 'date': date}