# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class NewAccountBonusReport(models.Model):
    _name = 'new.account.bonus.report'
    _auto = False
    _order = 'invoice_date asc'

    customer = fields.Many2one('res.partner', 'Customer Name')
    business_development = fields.Many2one('res.users', 'Business Development')
    customer_business_development = fields.Many2one('res.users', 'Customer Business Development')
    key_account = fields.Many2one('res.users', 'Key Account')
    customer_key_account = fields.Many2one('res.users', 'Customer Key Account')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order#')
    invoice_date = fields.Date('Invoice Date')
    invoice_status = fields.Char('Invoice Status')
    invoice_state = fields.Char('Status')
    amount_total = fields.Float('Total')
    months = fields.Integer('Months Ago First Order', group_operator="max")
    currency_id = fields.Many2one('res.currency', string='Currency')
    date_of_first_order = fields.Date('Date of First Order')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=False):
        fields = ['customer', 'business_development', 'key_account', 'sale_order_id', 'invoice_date', 'invoice_status',
                  'amount_total',
                  'months', 'currency_id', 'date_of_first_order']

        if orderby == '' or orderby is False:
            order_by = 'amount_total desc'
        else:
            order_by = orderby
        res = super(NewAccountBonusReport, self).read_group(domain, fields, groupby, offset, limit=limit,
                                                            orderby=order_by, lazy=lazy)
        return res

    # @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        business_development_id = self.env.context.get('business_development')
        key_account_id = self.env.context.get('key_account')

        if start_date and end_date:
            select_query = """
                SELECT ROW_NUMBER () OVER (ORDER BY so.id)  AS id, 
                        so.id                               AS sale_order_id, 
                        so.partner_id                       AS customer, 
                        so.user_id                          AS business_development,
                        so.account_manager                  AS key_account,
                        rp.user_id                          AS customer_business_development,
                        rp.account_manager_cust             AS customer_key_account,
                        ai.invoice_date                     AS invoice_date, 
                        CASE WHEN so.invoice_status = 'invoiced' then 'Fully Invoiced' END AS invoice_status,
                        CASE WHEN ai.state = 'posted' then 'Posted' END AS invoice_state,
                        ai.amount_total                     AS amount_total, 
                        X.months                            AS months,
                        ai.currency_id                      AS currency_id,
                        X.first_occurence                   AS date_of_first_order
                FROM public.sale_order so
                INNER JOIN
                    (SELECT sos.partner_id, MIN(aii.invoice_date) As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', MIN(aii.invoice_date))) AS months    
                        FROM public.sale_order sos
                        INNER JOIN 
                            public.account_move aii ON sos.name = aii.invoice_origin
                        GROUP BY sos.partner_id
                        Having MIN(aii.invoice_date) > '""" + str(end_date) + """ ')
                        
                        UNION
                        
                        ( SELECT sos.partner_id, aii.invoice_date As first_occurence,
                            DATE_PART('month', AGE(' """ + str(start_date) + """ ', aii.invoice_date)) AS months    
                        FROM public.sale_order sos 
                        INNER JOIN public.res_partner rep ON sos.partner_id= rep.id 
                        INNER JOIN public.account_move aii ON sos.name = aii.invoice_origin 
                        where rep.reinstated_date > ' """ + str(end_date) + """ ' and rep.reinstated_date is not null
                        GROUP BY sos.partner_id,aii.invoice_date
                        Having aii.invoice_date > ' """ + str(end_date) + """ ' )
                        
                    ) X
                        ON so.partner_id = X.partner_id
                    INNER JOIN 
                        public.account_move ai ON so.name = ai.invoice_origin AND ai.state in ('posted')
                    INNER JOIN 
                        public.res_partner rp ON so.partner_id = rp.id
                WHERE so.invoice_status = 'invoiced'                
                   """

            if business_development_id:
                select_query = select_query + " AND rp.user_id = '" + str(business_development_id) + "'"

            if key_account_id:
                select_query = select_query + " AND rp.account_manager_cust = '" + str(key_account_id) + "'"

            order_by = " ORDER BY ai.invoice_date asc"

            select_query = select_query + order_by

            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + select_query + " )")
        else:
            # This Code For only console error resolve purposr
            self.env.cr.execute('''
                             CREATE OR REPLACE VIEW %s AS (
                             SELECT  so.id AS id,
                                     so.name AS name
                             FROM sale_order so
                             )''' % (self._table)
                                )

    # @api.model_cr
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

    business_development = fields.Many2one('res.users', string="Business Development", index=True,
                                           domain="['|', ('active', '=', True), ('active', '=', False)]")

    key_account = fields.Many2one('res.users', string="Key Account", index=True,
                                  domain="['|', ('active', '=', True), ('active', '=', False)]")

    def download_excel_bd_new_account(self):

        start_date = self.string_to_date(str(self.start_date))
        end_date = start_date - datetime.timedelta(days=365)
        # start_date = start_date + datetime.timedelta(days=1)

        url = '/web/export/new_account_bonus_report_export/' + str(start_date) + '/' + str(end_date) + '/'

        if self.business_development and self.business_development is not None:
            url = url + str(self.business_development.id) + '/'
        else:
            url = url + str('none') + '/'

        if self.key_account and self.key_account is not None:
            url = url + str(self.key_account.id)
        else:
            url = url + str('none')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()
