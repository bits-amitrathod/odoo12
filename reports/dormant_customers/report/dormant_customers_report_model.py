import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.dormant_customers.dorm_cust_report_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        records = self.env['res.partner'].browse(docids)
        dates_picked = self.env['dormant_customers.popup'].search([('create_uid', '=', self._uid)], limit=1,
                                                                  order="id desc")

        if dates_picked.compute_at_date:
            date_range = str(dates_picked.start_date) + " - " + str(dates_picked.end_date)
        else:
            date_range = False

        return {
            'dateRange': date_range,
            'data': records}
