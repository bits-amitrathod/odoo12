#from pygments.lexer import default

from odoo import api, fields, models ,_
import datetime

class BrokerReportPopUp(models.TransientModel):
    _name = 'brokerreport.popup'
    _description = 'Broker Report PopUp'

    compute_at_date = fields.Selection([
        ('0', 'Show All '),
        ('1', 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default='0')
    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date",
                             default=(fields.date.today() - datetime.timedelta(days=31)))
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",
                           default=fields.Date.today())

    def open_table(self):

        action=self.env.ref('broker_report.action_report_broker_report').report_action([], data={'start_date' : self.start_date ,'end_date' : self.end_date })
        action.update({'target':'main'})
        return action
