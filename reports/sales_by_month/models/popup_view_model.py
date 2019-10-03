# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ProductSaleByCountPopUp(models.TransientModel):
    _name = 'salesbymonth.popup'
    _description = 'Sales By Month'



    end_date = fields.Date('To Date',default=(fields.date.today()),required=True)
    product_sku_code = fields.Many2one('product.product', 'Product SKU')

    def open_table(self):
        tree_view_id = self.env.ref('sales_by_month.list_view').id
        form_view_id = self.env.ref('sales_by_month.sales_by_month_form').id
        # if  self.end_date :
        #     self.end_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d") + datetime.timedelta(days=1)

        x_res_model = 'sales_by_month'
        # self.env[x_res_model].with_context(margins_context).delete_and_create()

        today=datetime.date(datetime.strptime(str(self.end_date), "%Y-%m-%d"))
        today=today.replace(day=1)
        end_of_month=today + relativedelta(months=1, days=-1)
        sixth_month=(today - relativedelta(day=1, months=5))
        cust_location_id = self.env['stock.location'].search([('name', '=', 'Customers')]).id
        select_query = " SELECT  ARRAY_AGG(DISTINCT stock_move.product_id) as product_id  FROM stock_picking INNER JOIN stock_move ON ( stock_picking.id =  stock_move.picking_id )" \
                       " WHERE stock_move.state='done' and stock_picking.state='done' and  stock_picking.date_done  BETWEEN  date('" + str(
            sixth_month) + "') AND date('" + str((end_of_month)) + "')" +" and stock_move.location_dest_id="+str(cust_location_id)

        self._cr.execute(select_query)
        product_id_list =self._cr.fetchall()
        margins_context = {'end_date': today}
        product_ids=[]
        if product_id_list:
            product_ids=(product_id_list[0])[0]
        # product_id_list = self._cr.execute(select_query)
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Sales By Month'),
            'res_model': 'product.product',
            'context':margins_context,
            'domain': [('id','in',product_ids)],
            'target': 'main'
        }
        if self.product_sku_code:
            action['domain'].append(('sku_code', '=', self.product_sku_code.sku_code))

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATETIME_FORMAT).date()

