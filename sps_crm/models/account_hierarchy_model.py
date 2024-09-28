# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
import logging

_logger = logging.getLogger(__name__)


class AccountHierarchyReport(models.Model):
    _name = 'account.hierarchy.report'
    _description = 'AccountHierarchyReport'

    _auto = False

    customer = fields.Many2one('res.partner', 'Customer Name')
    child_customer = fields.Many2one('res.partner', 'Customer Name')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=False):
        fields = ['customer','child_customer']

        if orderby == '' or orderby is False:
            order_by = 'customer'
        else:
            order_by = orderby
        res = super(AccountHierarchyReport, self).read_group(domain, fields, groupby, offset, limit=limit,
                                                            orderby=order_by, lazy=lazy)
        return res

    # @api.model_cr
    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, self._name.replace(".", "_"))

        start_date = self.env.context.get('start_date')
        end_date = self.env.context.get('end_date')

        if start_date and end_date:

            select_query2 = """
                       select ROW_NUMBER () OVER (ORDER BY res.partner_id)  AS id
                      , res.partner_id as child_customer ,res.acc_cust_parent as customer  from partner_link_tracker res
                        inner join res_partner resp on res.acc_cust_parent =resp.id       
                        """

            select_query = """ 
              WITH RECURSIVE cte_name AS(
	         select res.partner_id as child_customer ,res.acc_cust_parent as customer  from partner_link_tracker res
                        inner join res_partner resp on res.acc_cust_parent =resp.id   and res.partner_id=0
              UNION All
               select res.partner_id as child_customer ,res.acc_cust_parent as customer  from partner_link_tracker res
                        inner join res_partner resp on res.acc_cust_parent =resp.id   and res.partner_id!=0
        ) SELECT ROW_NUMBER () OVER (ORDER BY child_customer)  AS id , 
        child_customer,customer FROM cte_name  order by child_customer desc
            
            """
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

