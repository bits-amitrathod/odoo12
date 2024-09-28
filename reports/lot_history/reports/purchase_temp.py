
from odoo import api, models


class ReportPurchaseSalespersonWise(models.AbstractModel):
    _name = 'report.lot_history.purchase_report'
    _description = "Report lot_history Purchase Salesperson Wise"

    @api.model
    def _get_report_values(self, docids, data=None):
        lot_history = self.env['lot.history.report'].browse(docids)

        action= {
            'data': lot_history,
        }
        return action
