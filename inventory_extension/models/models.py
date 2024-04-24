
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class WarningPopup(models.TransientModel):
    _name = 'warning.popup.wizard'

    picking_warn_msg = fields.Char(string="Warning", compute="compute_warning")


class StockPickingMarkAllButton(models.Model):
    _inherit = "stock.picking"

    is_mark_all_button_visible = fields.Boolean(string="Mark all visibility", compute='_compute_visibility', store=False)
    acq_user_id = fields.Many2one('res.users', string='Acq  Manager', compute='_get_acq_manager')
    picking_warn_msg = fields.Char(string="Warning", compute="compute_warning")
    is_online = fields.Boolean(string="Is online", store=False, default=False)

    # This method help to display popup at page load
    def compute_warning(self):
        for rec in self:
            if rec.sale_id and rec.sale_id.team_id:
                rec.is_online = True
                # if rec.partner_id.picking_warn in ["warning","block"] and rec.partner_id.picking_warn_msg:
                #     rec.picking_warn_msg = str(rec.partner_id.picking_warn_msg)
                if self.getParent(rec.sale_id).picking_warn in ["warning","block"] and self.getParent(rec.sale_id).picking_warn_msg:
                    rec.picking_warn_msg = str(self.getParent(rec.sale_id).picking_warn_msg)
                else:
                    rec.picking_warn_msg = None

            else:
                rec.picking_warn_msg = None

    #TODO: try to remove deprecated method and update new methods but i face problems
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPickingMarkAllButton, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                        toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            if 'picking_warn_msg' in result['fields']:
                for rec in self:
                    result['fields']['picking_warn_msg']['value'] = rec.picking_warn_msg or ''
        return result



    def _get_acq_manager(self):
        for sp in self:
            if sp.origin and sp.origin is not None:
                purchase_order = self.env['purchase.order'].search([('name', '=', sp.origin)])
                if purchase_order and purchase_order.acq_user_id is not None and purchase_order.acq_user_id:
                    sp.acq_user_id = purchase_order.acq_user_id.id
                else:
                    sp.acq_user_id = None
            else:
                sp.acq_user_id = None




    def _compute_visibility(self):
        for pick in self:
            pick.is_mark_all_button_visible =  pick.sale_id.id and not pick.state in ['done','cancel']

    def getParent(self, saleOrder):
        return saleOrder.partner_id.parent_id if saleOrder.partner_id.parent_id else saleOrder.partner_id

    def action_button_mark_all_done(self):
        self.ensure_one()
        if self.sale_id and self.sale_id.team_id and self.getParent(self.sale_id).picking_warn in ["block"]:
            return {
                'name': _("Warning for %s") % self.getParent(self.sale_id).name,
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'warning.popup.wizard',
                'type': 'ir.actions.act_window',
                'context': {'default_picking_warn_msg': self.getParent(self.sale_id).picking_warn_msg},
                'target': 'new', }
        else:
            if self.sale_id.id:
                for lines in self.move_ids:
                    for line_items in lines.move_line_ids:
                        line_items.qty_done = line_items.reserved_uom_qty
