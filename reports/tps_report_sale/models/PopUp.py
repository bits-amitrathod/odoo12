# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'tps.popup.view'
    _description = "TPS Popup View"

    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")



    def open_table(self):
        tree_view_id = self.env.ref('tps_report_sale.tree_list_tps').id
        form_view_id = self.env.ref('tps_report_sale.form_list_tps').id
        margins_context = {'start_date': self.start_date, 'end_date': self.end_date}
        x_res_model = 'total_product_sale'
        self.env[x_res_model].with_context(margins_context).delete_and_create()

        # s_date = PopUp.string_to_date(str(self.start_date))
        # e_date = PopUp.string_to_date(str(self.end_date))

        filtered_sale_orders = self.env['sale.order'].search([('date_order', '>=', self.start_date),('date_order','<=', self.end_date)])

        product_ids = []
        for sale_order in filtered_sale_orders:
            for sale_order_line in sale_order.order_line:
                product_ids.append(sale_order_line.product_id.id)

        product_ids = list(set(product_ids))



        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree,form',
            'nameproduct_tmpl_id': _('Total Product Sales'),
            'res_model': x_res_model,
            'context':margins_context,
            'target': 'main'
        }

        return action

    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(str(date_string), DEFAULT_SERVER_DATETIME_FORMAT).date()
