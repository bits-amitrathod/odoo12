#
# from odoo import api, fields, models,_
# import logging
# from odoo.exceptions import ValidationError
#
# _logger = logging.getLogger(__name__)
#
# class ResConfigSettingsForPr(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     _logger.info('In ResConfigSettings for prioritization')
#     document_processing_count_setting = fields.Boolean(string="Document Processing Count Setting", default=True)
#     document_processing_count = fields.Integer(string="Document Processing Count")
#
#     @api.onchange('document_processing_count_setting')
#     def _onchange_document_processing_count_setting(self):
#         if self.document_processing_count_setting is False:
#             self.document_processing_count = 0
#
#     @api.onchange('document_processing_count')
#     def _onchange_document_processing_count(self):
#         if self.document_processing_count == 0:
#             raise ValidationError(_('Document Processing Count at least 1'))
#
#     @api.constrains('document_processing_count')
#     @api.one
#     def _check_document_processing_count(self):
#         if self.document_processing_count == 0:
#             raise ValidationError(_('Document Processing Count at least 1'))
#
#     @api.model
#     def get_values(self):
#         res = super(ResConfigSettingsForPr, self).get_values()
#         params = self.env['ir.config_parameter'].sudo()
#         document_processing_count = int(params.get_param('prioritization_engine.document_processing_count'))
#         document_processing_count_setting = params.get_param('prioritization_engine.document_processing_count_setting',
#                                                          default=True)
#         res.update(document_processing_count_setting=document_processing_count_setting,
#                    document_processing_count=document_processing_count)
#         return res
#
#     @api.multi
#     def set_values(self):
#         super(ResConfigSettingsForPr, self).set_values()
#         self.env['ir.config_parameter'].sudo().set_param("prioritization_engine.document_processing_count",
#                                                          self.document_processing_count)
#         self.env['ir.config_parameter'].sudo().set_param("prioritization_engine.document_processing_count_setting",
#                                                          self.document_processing_count_setting)