from odoo import api, fields, models, _
from odoo import api, fields, models, _
from datetime import date
from datetime import timedelta
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettingsForVoidedProducts(models.TransientModel):
    _inherit = 'res.config.settings'

    _logger.info('In ResConfigSettingsForVoidedProducts for prioritization')

    remove_voided_product_setting = fields.Boolean(string="Remove Voided Product Setting", default=True)
    remove_voided_product_count = fields.Integer(string="Remove Voided Product Count", default=30)


    @api.onchange('remove_voided_product_setting')
    def _onchange_remove_voided_product_count_setting(self):
        if self.remove_voided_product_setting is False:
            self.remove_voided_product_count = 0

    @api.onchange('remove_voided_product_count')
    def _onchange_remove_voided_product_count(self):
        if self.remove_voided_product_count == 0:
            raise ValidationError(_('Remove Product Count at least 1'))


    @api.model
    def get_values(self):
        res = super(ResConfigSettingsForVoidedProducts, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        remove_voided_product_count = int(params.get_param('prioritization_engine.remove_voided_product_count'))
        remove_voided_product_setting = params.get_param('prioritization_engine.remove_voided_product_setting',
                                                         default=True)

        res.update(remove_voided_product_setting=remove_voided_product_setting,
                   remove_voided_product_count=remove_voided_product_count)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettingsForVoidedProducts, self).set_values()

        self.env['ir.config_parameter'].sudo().set_param("prioritization_engine.remove_voided_product_count",
                                                         self.remove_voided_product_count)
        self.env['ir.config_parameter'].sudo().set_param("prioritization_engine.remove_voided_product_setting",
                                                         self.remove_voided_product_setting)

    def remove_voided_product_scheduler(self):

        params = self.env['ir.config_parameter'].sudo()

        remove_voided_product_count = int(params.get_param('prioritization_engine.remove_voided_product_count'))

        sps_customer_request = self.env['sps.customer.requests'].search([('create_date', '<=', str(date.today()))])

        for customer_request in sps_customer_request:
            create_date = fields.Date.from_string(customer_request.create_date)
            days = remove_voided_product_count
            old_create_date = date.today() - timedelta(days=days)

            if create_date == old_create_date:
                query = "Delete from sps_customer_requests WHERE date(create_date) = " "'" + str(
                    old_create_date) + "'" "and status = 'Voided'"

                self.env.cr.execute(query)
