# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class mtd_sales(models.Model):

    _name = 'mtd_sales'
    _auto = False
    _description = 'Mtd Sales'

    day_of_month = fields.Integer('Day')
    amount_total = fields.Float('Amount')

    def init(self):
        self.init_table()

    def init_table(self):
        tools.drop_view_if_exists(self._cr, 'mtd_sales')

        month = self.env.context.get('month')
        year = self.env.context.get('year')

        sql_query = """ CREATE VIEW mtd_sales AS ( 
            SELECT ROW_NUMBER () OVER (ORDER BY day_of_month) as id,  day_of_month as day_of_month,  CASE WHEN q.amount_total IS NULL THEN 0 ELSE q.amount_total END as amount_total
                FROM generate_series(1, 31) as day_of_month LEFT JOIN ( SELECT                              
                        EXTRACT(day FROM  so.date_order) as day_from_date, 
                        SUM(so.amount_total) as amount_total 
                        FROM sale_order so """
        if year is None and  month is None:
            month=1
            year=2018
        sql_query = sql_query + """ WHERE 
                    EXTRACT(month FROM  so.date_order) = """ + str(month) + """ AND 
                    EXTRACT(year FROM so.date_order) = """ + str(year) + """  AND so.state = 'sale'                           
                   GROUP BY EXTRACT(day FROM  so.date_order)) q                       
                   ON q.day_from_date = day_of_month """

        sql_query = sql_query + """ ) """

        self._cr.execute(sql_query)

    def select_query(self):
        return """ SELECT 
        ROW_NUMBER () OVER (ORDER BY EXTRACT(day FROM  so.date_order)) as id,
        EXTRACT(day FROM so.date_order) as day_of_month,  
        so.amount_total as amount_total """

    def from_clause(self):
        return """
            FROM sale_order so 
        """

    def where_clause(self, year, month):
        _logger.info('year: %r, month: %r', str(year), str(month))
        return """
            WHERE 
        EXTRACT(month FROM  so.date_order) = """ + str(month) + """ AND 
        EXTRACT(year FROM so.date_order) = """ + str(year) + """ AND 
        so.state = 'sale'
        """
