
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_expiration_date = fields.Boolean(string='Lot expiration dates', default_model = 'res.config.settings')

    # @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            website_expiration_date=get_param('website_sales.website_expiration_date')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('website_sales.website_expiration_date', self.website_expiration_date)