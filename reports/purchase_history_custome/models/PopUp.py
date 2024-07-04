# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'popup.view.model.purchase.history'
    _description = "Purchase history popup model"


    start_date = fields.Date('Start Date' ,required=True)
    end_date = fields.Date(string="End Date" ,required=True)
    product_id = fields.Many2many('product.product', string="Products")
    contract_id = fields.Many2many('contract.contract', string='Contract')
    category_id = fields.Many2many('res.partner.category', string='Tag')
    vendor_id = fields.Many2one('res.partner', string='Vendor')

    # compute_at_date = fields.Selection([
    #     (0, 'Show All'),
    #     (1, 'Date Range')
    # ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")


    def open_table(self):

        tree_view_id = self.env.ref('purchase_history_custome.form_list').id
        form_view_id = self.env.ref('purchase_history_custome.form_cust_view').id
        if self.end_date:
            end_date = datetime.datetime.strptime(str(self.end_date), "%Y-%m-%d")
            end_date = end_date + datetime.timedelta(days=1)

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Purchase History'),
            'res_model': 'purchase.order.line',
            'context': {'start_date':self.start_date,'end_date':self.end_date},
            'domain': [('state','=','purchase'),
                       ('date_order', '>=', self.start_date),('date_order', '<=', self.end_date),
                       ('qty_received', '>', 0)
                       ],
        }
        if self.contract_id:
            action['domain'].append(('partner_id.contract', 'in', self.contract_id.ids))
        if self.product_id:
            action['domain'].append(('product_id','in', self.product_id.ids))
        if self.vendor_id:
            action['domain'].append(('partner_id','=', self.vendor_id.id))
        if self.category_id:
            action['domain'].append(('partner_id.category_id','in', self.category_id.ids))
        action.update({'target': 'main'})
        return action


