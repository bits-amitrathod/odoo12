import logging
from odoo import api, fields, models
from odoo.tools import float_repr
from datetime import datetime

log = logging.getLogger(__name__)


class Discount():
    sale_order = ''
    customer = ''
    confirmation_date = 0
    amount = 0
    discount_amount = 0
    total_amount = 0


class ReportProductVendorList(models.AbstractModel):
    _name = 'report.bonus_report.bonusreport_temp_test'
    _description = "Report Product VendorList Bonus"

    @api.model
    def _get_report_values(self, docids, data=None):

        popup = self.env['bonusreport.popup'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")

        if popup.compute_at_date:
            date = datetime.strptime(str(popup.start_date), '%Y-%m-%d').strftime('%m/%d/%Y') + " - " + datetime.strptime(
                str(popup.end_date), '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            date = False

        return {'data': self.env['purchase.order'].with_context(vendor_offer_data=True).browse(docids), 'date': date}