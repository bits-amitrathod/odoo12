from odoo import api, fields, models


class SaleSalespersonReport(models.Model):
    _inherit = "sale.order"

    start_date = fields.Date('Start Date' , compute = '_compute_date', store=False)
    end_date = fields.Date(string="End Date", store=False)

    def _compute_date(self):
        for order in self:
            if self.env.context.get('start_date'):
                order.start_date = (fields.Datetime.from_string(self.env.context.get('start_date')).date())
                order.end_date = (fields.Datetime.from_string(self.env.context.get('end_date')).date())
