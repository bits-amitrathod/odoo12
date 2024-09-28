from odoo import api, models


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.pick_report.pick_tmpl'
    _description = "Report Pick Report model template"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'data': data,
        }