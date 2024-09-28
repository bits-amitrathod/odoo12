import logging
from odoo import api, fields, models

log = logging.getLogger(__name__)


class ReportProductSaleByCount(models.AbstractModel):
    _name = 'report.dormant_customers.dorm_cust_report_temp'
    _description = "Report dormant_customers Product Sale By Count"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['res.partner'].browse(docids)
        dates_picked = self.env['dormant_customers.popup'].search([('create_uid', '=', self._uid)], limit=1,
                                                                  order="id desc")



        return {
            'dateRange': dates_picked,
            'data': records}
