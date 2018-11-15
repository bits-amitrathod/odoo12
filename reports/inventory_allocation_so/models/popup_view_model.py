from odoo import api, fields, models ,_
import datetime
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat, misc

_logger = logging.getLogger(__name__)

class TrendingReportListPopUp(models.TransientModel):
    _name = 'inventory.so_popup'
    _description = 'Inventory Allocation Report List PopUp'

    compute_at_date = fields.Selection([
        (0, 'Show All '),
        (1, 'Date Range ')
    ], string="Compute", help="Choose to analyze the Show Summary or from a specific date in the past.",default=0)
    group_by = fields.Selection([
        ('order_id', 'Sale'),
    ], string="Group By", default='order_id', required=True, _defaluts={'field_name': 'sale', })
    start_date = fields.Date('Start Date', help="Choose a date to get the Discount Summary at that  Start date",)
    end_date = fields.Date('End Date', help="Choose a date to get the Discount Summary at that  End date",)

    def open_table(self):
        #print(self.env.ref('inventory__allocation_so.view_inv_all_so_tree').id)
        tree_view_id = self.env.ref('inventory_allocation_so.view_inv_all_so_tree').id
        form_view_id = self.env.ref('inventory_allocation_so.inv_sale_order_form_view')


        if self.compute_at_date:
            s_date = TrendingReportListPopUp.string_to_date(str(self.start_date))
            e_date = TrendingReportListPopUp.string_to_date(str(self.end_date))
        else:
            s_date=None
            e_date=None

        margins_context = {'s_date': s_date, 'e_date': e_date, 'group_by': self.group_by}
        group_by_domain = ['order_id']
        x_res_model = 'inventory.allocation_so'

        self.env[x_res_model].with_context(margins_context).delete_and_create()

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id.id, 'form')],
            'name': _('Inventory Allocation For SO'),
            'context': {'group_by': group_by_domain, 'order_by': group_by_domain},
            'res_model': x_res_model,
            'target': 'main'
        }
        # action.update({'target': 'main'})
        return action



    @staticmethod
    def string_to_date(date_string):
        return datetime.datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()