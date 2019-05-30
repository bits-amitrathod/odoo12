
from odoo import api,fields, models


class RmaReport(models.AbstractModel):
    _name = 'report.rma_report.rma_tmpl'

    @api.model
    def _get_report_values(self, docids, data=None):

        return {
            'data': data,
        }