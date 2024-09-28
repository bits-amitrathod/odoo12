import logging
from odoo import api, fields, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_discount_summary.discountsummary_temp_test'
    _description = "Report Sales Salesperson Wise"

    @api.model
    def _get_report_values(self, docids, data=None):
        popup = self.env['popup.discount.summary'].search([('create_uid', '=', self._uid)], limit=1,
                                                          order="id desc")


        return {
            'data': self.env['sale.order'].browse(docids),
            'popup': popup
        }
