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

