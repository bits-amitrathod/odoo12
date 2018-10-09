from odoo import api, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.receiving_list.receiving_list_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        return {
            'doc_ids': data.get('ids'),
            'doc_model': data.get('model'),
            'data': data['form'],
        }