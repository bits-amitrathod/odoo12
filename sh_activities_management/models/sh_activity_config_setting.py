# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_planned_table = fields.Integer(default=10)
    sh_all_table = fields.Integer(default=10)
    sh_completed_table = fields.Integer(default=10)
    sh_due_table = fields.Integer(default=10)
    sh_cancel_table = fields.Integer(default=10)
    sh_display_multi_user = fields.Boolean()
    sh_display_all_activities_counter = fields.Boolean(default=True)
    sh_display_planned_activities_counter = fields.Boolean(default=True)
    sh_display_completed_activities_counter = fields.Boolean(default=True)
    sh_display_overdue_activities_counter = fields.Boolean(default=True)
    sh_display_cancelled_activities_counter = fields.Boolean(default=True)
    sh_display_all_activities_table = fields.Boolean(default=True)
    sh_display_planned_activities_table = fields.Boolean(default=True)
    sh_display_completed_activities_table = fields.Boolean(default=True)
    sh_display_overdue_activities_table = fields.Boolean(default=True)
    sh_display_cancelled_activities_table = fields.Boolean(default=True)
    sh_display_activity_reminder = fields.Boolean(default=True)
    sh_document_model = fields.Boolean()
    sh_document_model_ids = fields.Many2many('ir.model', 'sh_ir_model_res_company_rel', 'sh_company_id', 'sh_model_id',string="Document Models ")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_planned_table = fields.Integer(related='company_id.sh_planned_table',readonly=False)
    sh_all_table = fields.Integer(related='company_id.sh_all_table',readonly=False)
    sh_completed_table = fields.Integer(related='company_id.sh_completed_table',readonly=False)
    sh_due_table = fields.Integer(related='company_id.sh_due_table',readonly=False)
    sh_cancel_table = fields.Integer(related='company_id.sh_cancel_table',readonly=False)
    sh_display_multi_user = fields.Boolean(related='company_id.sh_display_multi_user',readonly=False)
    sh_display_all_activities_counter = fields.Boolean(related='company_id.sh_display_all_activities_counter',readonly=False)
    sh_display_planned_activities_counter = fields.Boolean(related='company_id.sh_display_planned_activities_counter',readonly=False)
    sh_display_completed_activities_counter = fields.Boolean(related='company_id.sh_display_completed_activities_counter',readonly=False)
    sh_display_overdue_activities_counter = fields.Boolean(related='company_id.sh_display_overdue_activities_counter',readonly=False)
    sh_display_cancelled_activities_counter = fields.Boolean(related='company_id.sh_display_cancelled_activities_counter',readonly=False)
    sh_display_all_activities_table = fields.Boolean(related='company_id.sh_display_all_activities_table',readonly=False)
    sh_display_planned_activities_table = fields.Boolean(related='company_id.sh_display_planned_activities_table',readonly=False)
    sh_display_completed_activities_table = fields.Boolean(related='company_id.sh_display_completed_activities_table',readonly=False)
    sh_display_overdue_activities_table = fields.Boolean(related='company_id.sh_display_overdue_activities_table',readonly=False)
    sh_display_cancelled_activities_table = fields.Boolean(related='company_id.sh_display_cancelled_activities_table',readonly=False)
    sh_display_activity_reminder = fields.Boolean(related='company_id.sh_display_activity_reminder',readonly=False)
    sh_document_model = fields.Boolean(related='company_id.sh_document_model',readonly=False)
    sh_document_model_ids = fields.Many2many('ir.model',related='company_id.sh_document_model_ids',readonly=False,string="Document Models")

    @api.onchange('sh_document_model')
    def onchange_sh_document_model(self):
        if self.sh_document_model:
            models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')])
            document_models = []
            for model in models:
                if not model.model.startswith('ir.'):
                    document_models.append(model.id)
            return {'domain': {'sh_document_model_ids': [('id', 'in', document_models)]}}
        else:
            self.sh_document_model_ids = False

    def action_update_activity_data(self):
        activities = self.env['mail.activity'].sudo().search([('active','!=',False),('activity_cancel','=',False),('activity_done','=',False)])
        if activities:
            for activity in activities:
                activity.active = True
                activity.onchange_state()

