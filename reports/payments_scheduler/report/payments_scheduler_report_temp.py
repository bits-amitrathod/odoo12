import logging
from odoo import api, fields, models


class payments_scheduler_report(models.AbstractModel):
    _name = 'report.payments_scheduler.payments_scheduler_temp_test'
    _description = "Payment Scheduler Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = self.env['account.move'].browse(docids)
        action = {'data': data}
        return action
