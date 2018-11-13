
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettingsForPr(models.TransientModel):
    _inherit = 'res.config.settings'

    _logger.info('In ResConfigSettings for prioritization')
    document_processing_count_setting = fields.Boolean(string="Document Processing Count Setting", default=True)
    document_processing_count = fields.Integer(string="Document Processing Count", default=3)