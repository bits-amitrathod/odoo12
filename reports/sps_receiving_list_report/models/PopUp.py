# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
from odoo import _

_logger = logging.getLogger(__name__)


class PopUp(models.TransientModel):
    _name = 'sps_receive_popup.view.model'

    start_date = fields.Date('Start Date')
    end_date = fields.Date(string="End Date")

    compute_at_date = fields.Selection([
        (0, 'Show All'),
        (1, 'Date Range')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")

    def open_table(self):
        tree_view_id = self.env.ref('sps_receiving_list_report.form_list_sps').id
        # form_view_id = self.env.ref('stock.view_picking_form').id

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': _('SPS Receiving List'),
            'res_model': 'stock.move.line',
            'domain': [('state', '=', 'done'), ('move_id.purchase_line_id', '!=', False)],
            'context': {"search_default_product_group": 1},
            'target': 'main'
        }

        if self.compute_at_date:
            action['domain'].append(('date', '>=', self.start_date))
            action['domain'].append(('date', '<=', self.end_date))
            return action
        else:
            return action
