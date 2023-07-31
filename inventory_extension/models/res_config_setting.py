from odoo import api, fields, models, _
from odoo.osv import osv
import warnings
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_stock_production_lot = fields.Boolean(string="Lots & Serial Numbers", default=True,
                                                implied_group='stock.group_production_lot')
    module_product_expiry = fields.Boolean(string="Expiration Dates",
                                           help="Track following dates on lots & serial numbers: best before, removal, end of life, alert. \n Such dates are set automatically at lot/serial number creation based on values set on the product (in days).")
    production_lot_alert_days = fields.Integer(string="Alert Days")
    production_lot_alert_settings = fields.Boolean(string="Alert Setting", default=True)

    @api.onchange('module_product_expiry')
    def _onchange_module_product_expiry(self):
        if self.module_product_expiry:
            self.production_lot_alert_settings = True

        else:
            self.production_lot_alert_settings = False
            self.production_lot_alert_days = 0

    @api.onchange('production_lot_alert_settings')
    def _onchange_production_lot_alert_settings(self):
        if self.production_lot_alert_settings is False:
            self.production_lot_alert_days = 0

    @api.onchange('production_lot_alert_days')
    def _onchange_production_lot_alert_days(self):
        if self.production_lot_alert_days > 366:
            self.production_lot_alert_days = 0

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        production_lot_alert_days = int(params.get_param('inventory_extension.production_lot_alert_days'))
        production_lot_alert_settings = params.get_param('inventory_extension.production_lot_alert_settings',
                                                         default=True)
        group_stock_production_lot = params.get_param('inventory_extension.group_stock_production_lot')
        module_product_expiry = params.get_param('inventory_extension.module_product_expiry')
        res.update(production_lot_alert_settings=production_lot_alert_settings,
                   production_lot_alert_days=production_lot_alert_days,
                   group_stock_production_lot=group_stock_production_lot, module_product_expiry=module_product_expiry)
        return res

    #@api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_days",
                                                         self.production_lot_alert_days)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_settings",
                                                         self.production_lot_alert_settings)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.group_stock_production_lot",
                                                         self.group_stock_production_lot)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.module_product_expiry",
                                                         self.module_product_expiry)

class WarningPopup(models.TransientModel):
    _name = 'warning.popup.wizard'

    picking_warn_msg = fields.Char(string="Warning", compute="compute_warning")


class StockPickingMarkAllButton(models.Model):
    _inherit = "stock.picking"

    is_mark_all_button_visible = fields.Boolean(string="Mark all visibility", compute='_compute_visibility', store=False)
    acq_user_id = fields.Many2one('res.users', string='Acq  Manager', compute='_get_acq_manager')
    picking_warn_msg = fields.Char(string="Warning", compute="compute_warning")
    is_online = fields.Boolean(string="Is online", store=False, default=False)

    def compute_warning(self):
        for rec in self:
            if rec.sale_id and rec.sale_id.team_id and rec.sale_id.team_id.name in ["Website", "My In-Stock Report", "Sales", "Prioritization"]:
                rec.is_online = True
                # if rec.partner_id.picking_warn in ["warning","block"] and rec.partner_id.picking_warn_msg:
                #     rec.picking_warn_msg = str(rec.partner_id.picking_warn_msg)
                if rec.sale_id.partner_id.picking_warn in ["warning","block"] and rec.sale_id.partner_id.picking_warn_msg:
                    rec.picking_warn_msg = str(rec.sale_id.partner_id.picking_warn_msg)
                else:
                    rec.picking_warn_msg = None

            else:
                rec.picking_warn_msg = None

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

    def action_button_mark_all_done(self):
        self.ensure_one()
        if self.sale_id and self.sale_id.team_id and self.sale_id.team_id.name in ["Website", "My In-Stock Report", "Sales", "Prioritization"] and self.sale_id.partner_id.picking_warn in ["block"]:
            return {
                'name': _("Warning for %s") % self.sale_id.partner_id.name,
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'warning.popup.wizard',
                'type': 'ir.actions.act_window',
                'context': {'default_picking_warn_msg': self.sale_id.partner_id.picking_warn_msg},
                'target': 'new', }
        else:
            if self.sale_id.id:
                for lines in self.move_lines:
                    for line_items in lines.move_line_ids:
                        line_items.qty_done = line_items.product_uom_qty