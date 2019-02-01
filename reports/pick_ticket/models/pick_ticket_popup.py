from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportPickTicketGroupByOrderDate(models.TransientModel):
    _name = 'popup.pick.ticket'
    _description = 'Pick Ticket Group By Order'

    compute_at_date = fields.Selection([
        (0, 'Order'),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    start_date = fields.Date('Start Date', default=fields.date.today() - datetime.timedelta(days=30), required=True)

    end_date = fields.Date('End Date', default=fields.date.today(), required=True)

    picking_id = fields.Many2many('stock.picking', string='Pick Number',domain=[('sale_id.id', '!=', False)])

    def open_table(self):

        tree_view_id = self.env.ref('pick_ticket.pick_report_list_view').id
        form_view_id = self.env.ref('pick_ticket.pick_ticket_form_view').id

        res_model = 'report.pick.ticket'
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree',
            'name': 'Pick Ticket',
            'res_model': res_model,
            'context': {'group_by': 'picking_id'},
            'domain': []
        }

        if self.compute_at_date:
            if self.start_date:
                action["domain"].append(('scheduled_date', '>=', self.start_date))

            if self.end_date:
                action["domain"].append(
                    ('scheduled_date', '<=', self.string_to_date(str(self.end_date)) + datetime.timedelta(days=1)))

        else:
            if len(self.picking_id.ids) > 0:
                action["domain"].append(('picking_id', 'in', self.picking_id.ids))

        if self.compute_at_date:
            return action
        else:
            return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
