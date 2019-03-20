from odoo import api, fields, models, _
import datetime


class DiscountSummaryPopUp(models.TransientModel):
    _name = 'popup.discount.summary'
    _description = 'Discount Summary PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    partner_id = fields.Many2one('res.partner', string='Customer')
    sale_order = fields.Many2one('sale.order', string='Sale Order')

    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date",
                                 default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",
                               default=fields.Datetime.now)

    def open_table(self):
        tree_view_id = self.env.ref('report_discount_summary.form_list').id
        form_view_id = self.env.ref('sale.view_order_form').id
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Discount Summary'),
            'res_model': 'sale.order',
            'domain': [('state', 'in', ('sale', 'done'))],
        }

        if self.sale_order:
            action['domain'].append(('id', '=', self.sale_order.id))

        if self.partner_id:
            action['domain'].append(('partner_id', '=', self.partner_id.id))

        if self.compute_at_date:
            action['domain'].extend([('confirmation_date', '>=', self.start_date), ('confirmation_date', '<=', self.end_date)])
            return action
        else:
            return action
