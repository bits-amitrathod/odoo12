from odoo import api, models


class OnHandByDateReportModel(models.AbstractModel):
    _name = 'report.on_hand_by_expiry.templ'

    @api.model
    def get_report_values(self, docids, data=None):
        on_hand_by_expiration_date_stock_list = self.env['on_hand_by_expiry'].browse(docids)

        action = self.env.ref('on_hand_by_expiry.action_report_on_hand_by_expiry').report_action([],
                                            data=on_hand_by_expiration_date_stock_list)
        action.update({'target': 'main'})

        return action