from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.on_hand_by_date.on_hand_by_date_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': data['form'],
        }