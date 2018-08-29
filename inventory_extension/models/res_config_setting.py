from odoo import api, fields, models
from odoo.osv import osv
import warnings
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    group_stock_production_lot = fields.Boolean(string ="Lots & Serial Numbers", default=True,implied_group='stock.group_production_lot')
    module_product_expiry = fields.Boolean(string ="Expiration Dates",default=True,
        help="Track following dates on lots & serial numbers: best before, removal, end of life, alert. \n Such dates are set automatically at lot/serial number creation based on values set on the product (in days).")
    production_lot_alert_days = fields.Integer(string="Alert Days")
    production_lot_alert_settings = fields.Boolean(string="Alert Setting",default=True)

    @api.onchange('group_stock_production_lot')
    def _onchange_group_stock_production_lot(self):
        if self.group_stock_production_lot:
            self.module_product_expiry = True
            self.production_lot_alert_settings = True
        else:
            self.module_product_expiry = False
            self.production_lot_alert_settings = False
            self.production_lot_alert_days = 0

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
        if self.production_lot_alert_days >366:
            self.production_lot_alert_days = 0

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        production_lot_alert_days = int(
            params.get_param('inventory_extension.production_lot_alert_days'))
        production_lot_alert_settings = params.get_param('inventory_extension.production_lot_alert_settings',  default=True)
        res.update(production_lot_alert_settings=production_lot_alert_settings, production_lot_alert_days=production_lot_alert_days,)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_days",
                                                         self.production_lot_alert_days)
        self.env['ir.config_parameter'].sudo().set_param("inventory_extension.production_lot_alert_settings",
                                                         self.production_lot_alert_settings)
