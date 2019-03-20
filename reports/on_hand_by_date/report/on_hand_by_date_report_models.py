from odoo import api, models


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.on_hand_by_date.on_hand_by_date_temp'

    @api.model
    def get_report_values(self, docids, data=None):
        products = self.env['report.on.hand.by.date'].browse(docids)
        popup = self.env['popup.on_hand_by_date'].search([('create_uid', '=', self._uid)], limit=1, order="id desc")
        return {'products': products, 'popup': popup}
