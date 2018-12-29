import time

from odoo import api, fields, models, _
import datetime


class DateGen:

    def getFirstOfMonth(self):
        dtDateTime = fields.date.today()
        ddays = int(dtDateTime.strftime("%d")) - 1  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta

    def getLastOfMonth(self):
        dtDateTime = fields.date.today()
        next_month = dtDateTime.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
        return next_month - datetime.timedelta(days=next_month.day)

    def getFirstDayOfLastMonth(self):
        dtDateTime = self.getLastDayOfLastMonth()
        ddays = int(dtDateTime.strftime("%d")) - 1  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta

    def getLastDayOfLastMonth(self):
        dtDateTime = self.getFirstOfMonth()
        ddays = int(dtDateTime.strftime("%d"))  # days to subtract to get to the 1st
        delta = datetime.timedelta(days=ddays)  # create a delta datetime object
        return dtDateTime - delta


class DiscountSummaryPopUp(models.TransientModel):
    _name = 'compbysale.popup'
    _description = 'Compare Sale By Month'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.")

    date_gen = DateGen()

    current_start_date = fields.Date('Current month Start Date', default=date_gen.getFirstOfMonth())
    current_end_date = fields.Date('Current month End Date', default=date_gen.getLastOfMonth())

    last_start_date = fields.Date('Last Month Start Date',default=date_gen.getFirstDayOfLastMonth())
    last_end_date = fields.Date('Last Month End Date', default=date_gen.getLastDayOfLastMonth())

    def open_table(self):
        tree_view_id = self.env.ref('report_compare_sale_by_month.list_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id
        if self.compute_at_date:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Compare Sales By Month'),
                'res_model': 'product.product',
                'context': {'current_start_date': self.current_start_date, 'current_end_date': self.current_end_date,
                            'last_start_date': self.last_start_date, 'last_end_date': self.last_end_date},
                'domain': [('type', 'in', ['product'])],
            }
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Compare Sales By Month'),
                'res_model': 'product.product',
                'context': {'current_start_date': self.current_start_date, 'current_end_date': self.current_end_date,
                            'last_start_date': self.last_start_date, 'last_end_date': self.last_end_date},
                'domain': [('type', 'in', ['product'])],
            }
            return action
