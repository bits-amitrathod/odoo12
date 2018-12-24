import logging
from odoo import api, fields, models


class ReportSalesSalespersonWise(models.AbstractModel):
    _name = 'report.report_discount_summary.discountsummary_temp_test'

    @api.model
    def get_report_values(self, docids, data=None):
        popup = self.env['popup.discount.summary'].search([('create_uid', '=', self._uid)], limit=1,
                                                          order="id desc")
        if popup.compute_at_date:
            date = popup.start_date + " to " + popup.end_date
        else:
            date = False

        return {
            'data': self.env['sale.order'].browse(docids),
            'date': date
        }
