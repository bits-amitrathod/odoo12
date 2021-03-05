# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class NewAccountBonusReport(models.Model):
    _name = 'new.account.bonus.report'
    _auto = False
    _order = 'business_development'

    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    date_invoice = fields.Date('Invoice Date')
    invoice_status = fields.Char('Status')
    amount_total = fields.Float('Total')
    months = fields.Integer('Month', group_operator="max")
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        business_development_id = self.env.context.get('business_development')

        if start_date and end_date:
            select_query = """
                SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                        so.id                               AS sale_order_id, 
                        so.partner_id                       AS customer, 
                        so.user_id                          AS business_development,
                        ai.date_invoice                     AS date_invoice, 
                        CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status, 
                        ai.amount_total                     AS amount_total, 
                        X.months                            AS months,
                        ai.currency_id                      AS currency_id
                FROM public.sale_order so
                INNER JOIN
                    (
                        SELECT sos.partner_id, MIN(aii.date_invoice) As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.date_invoice))) AS months    
                        FROM public.sale_order sos
                        INNER JOIN 
                            public.account_invoice aii ON sos.name = aii.origin
                        GROUP BY sos.partner_id
                        Having MIN(aii.date_invoice) >= '""" + str(end_date) + """ ') X
                        ON so.partner_id = X.partner_id
                    INNER JOIN 
                        public.account_invoice ai ON so.name = ai.origin AND ai.date_invoice >= X.first_occurence
                WHERE so.invoice_status = 'invoiced' AND ai.state = 'paid' AND ai.date_invoice >= '                
                   """ + str(end_date) + """'"""

            if business_development_id:
                select_query = select_query + "AND so.user_id = '" + str(business_development_id) + "'"

            order_by = " ORDER BY ai.date_invoice desc"

            select_query = select_query + order_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )")

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class NewAccountBonusReportExport(models.TransientModel):
    _name = 'new.account.bonus.report.export'

    start_date = fields.Date('Start Date', default=fields.date.today(), required=True,
                             help="Choose a date to get the New Account Bonus Report at that Start date")

    business_development = fields.Many2one('res.users', string="Business Development", index=True)

    def download_excel_bd_new_account(self):

        start_date = self.string_to_date(str(self.start_date))
        end_date = start_date - datetime.timedelta(days=365)
        start_date = start_date + datetime.timedelta(days=1)

        if self.business_development and self.business_development is not None:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_bonus_report_export/' + str(start_date) + '/' + str(end_date) + '/' +
                       str(self.business_development.id),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_bonus_report_export/' + str(start_date) + '/' + str(end_date) + '/' + str(
                    'none'),
                'target': 'new'
            }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
