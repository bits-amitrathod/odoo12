# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import datetime
from odoo.tools import float_repr
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'sps_recieve_popup.view.model'


    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")


    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")


    def open_table(self):
        tree_view_id = self.env.ref('sps_recieving_list_report.form_list_sps').id
        form_view_id = self.env.ref('stock.view_picking_form').id
        if self.compute_at_date:

            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('SPS Recieving List'),
                'res_model': 'stock.picking',
                'domain': [('date', '>=', self.start_date),('date', '<=', self.end_date)],
            }
            action.update({'target': 'main'})
            return action
        else:
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'),(form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('SPS Recieving List'),
                'res_model': 'stock.picking',

            }
            action.update({'target': 'main'})
            return action




