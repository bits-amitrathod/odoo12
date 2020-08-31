# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class NewAccountByMonthByNa(models.Model):
    _name = 'report.na.new.account'
    _auto = False

    onboard_date = fields.Datetime('Onboard Date')
    customer = fields.Many2one('res.partner', 'Customer Name')
    national_account = fields.Many2one('res.users', 'National Account')

    @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')
        if start_date and end_date :
            select_query = """
                       SELECT
                            ROW_NUMBER () OVER (ORDER BY RP.id) AS id,
                            RP.id                               AS customer,
                            COALESCE(RP.reinstated_date, RP.create_date)       AS onboard_date,
                            RP.national_account_rep                          AS national_account
            
                       FROM public.res_partner RP
            
                        WHERE RP.customer = true AND RP.active = true 
                        AND RP.national_account_rep IS NOT NULL AND RP.parent_id IS NULL
            
            
                   """

            # select_query = select_query + " AND RP.create_date >= COALESCE(RP.reinstated_date, RP.create_date) " \
            #                               " AND RP.create_date BETWEEN '" + str(start_date) + "' " + " AND '" + str(
            #     end_date) + "' "
            
            select_query = select_query + " AND COALESCE(RP.reinstated_date, RP.create_date) BETWEEN '" + str(start_date) + "' " + " AND '" + str(
                end_date) + "' "
            
            
            national_account_id = self.env.context.get('national_account')
            
            
            if national_account_id:
                select_query = select_query + "AND RP.national_account_rep = '" + str(national_account_id) + "'"
            
            
            # group_by = """ GROUP BY RP.id"""
            
            sql_query = select_query  #+ group_by
            
            self._cr.execute("CREATE VIEW " + self._name.replace(".", "_") + " AS ( " + sql_query + " )")
            

    @api.model_cr
    def delete_and_create(self):
        self.init_table()

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATE_FORMAT).date()


# Export code

class NewAccountByMonthByNaExport(models.TransientModel):
    _name = 'report.na.new.account.export'

    start_date = fields.Date('Start Date', default=(fields.date.today() - datetime.timedelta(days=31)),
                             help="Choose a date to get the New Account By Month By National Account at that  Start date")
    end_date = fields.Date('End Date', default=fields.date.today(),
                           help="Choose a date to get the New Account By Month By National Account at that  End date")
    national_account = fields.Many2one('res.users', string="National Account", index=True)

    def download_excel_na_new_account(self):

        e_date = self.string_to_date(str(self.end_date))
        e_date = e_date + datetime.timedelta(days=1)
        s_date = self.string_to_date(str(self.start_date))

        if self.national_account and self.national_account is not None:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_by_month_by_na_export/' + str(s_date) + '/' + str(e_date) + '/' +
                       str(self.national_account.id),
                'target': 'new'
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/export/new_account_by_month_by_na_export/' + str(s_date) + '/' + str(e_date) + '/' + str('none'),
                'target': 'new'
            }


    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()

