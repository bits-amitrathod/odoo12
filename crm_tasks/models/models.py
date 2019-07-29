# -*- coding: utf-8 -*-
# #
from odoo import models, fields, api,tools
from dateutil.relativedelta import relativedelta

class MailActivityCustom(models.Model):
    _inherit = 'mail.activity'
    names=fields.Many2one('crm.lead', store=True)

    # @api.onchange('names')
    # @api.model
    def default_get_custom(self):
    #     super(MailActivityCustom, self).default_get(fields)
        self.res_model_id = 272
        self.res_model='crm.lead'
        # for activity in fields:
        #     if not activity or 'res_model_id' in activity and res.get('res_model'):
                # res['res_model_id'] = self.env['ir.model']._get(res['res_model']).id

    # def onchange_names(self):
    #     if self.names:
    #     self.res_model_id = 272
    #     self.res_model='crm.lead'
    #     self.res_id=46
    #

    #
    #
        # res = super(MailActivity, self).default_get(fields)
        # if not fields or 'res_model_id' in fields and res.get('res_model'):
        #     res['res_model_id'] = self.env['ir.model']._get(res['res_model']).id


    # @api.model
    # def default_get(self, fields):
    #     res = super(MailActivity, self).default_get(fields)
    #     if not fields or 'res_model_id' in fields and res.get('res_model'):
    #         res['res_model_id'] = self.env['ir.model']._get(res['res_model']).id
    #     return res






    # @api.onchange('activity_type_id')
    # def _onchange_activity_type_id(self):
    #     if self.activity_type_id:
    #         self.summary = self.activity_type_id.summary
    #         Date.context_today is correct because date_deadline is a Date and is meant to be
    #         expressed in user TZ
    #         base = fields.Date.context_today(self)
    #         if self.activity_type_id.delay_from == 'previous_activity' and 'activity_previous_deadline' in self.env.context:
    #             base = fields.Date.from_string(self.env.context.get('activity_previous_deadline'))
    #         self.date_deadline = base + relativedelta(**{self.activity_type_id.delay_unit: self.activity_type_id.delay_count})


    # @api.model
    # def default_get(self, fields):
    #     res = super(MailActivity, self).default_get(fields)
    #     if not fields or 'res_model_id' in fields and res.get('res_model'):
    #         res['res_model_id'] = self.env['ir.model']._get(res['res_model']).id
    #     return res



    # @api.multi
    # def action_create_calendar_event(self):
    #     self.ensure_one()
    #     action = self.env.ref('calendar.action_calendar_event').read()[0]
    #     action['context'] = {
    #         'default_activity_type_id': self.activity_type_id.id,
    #         'default_res_id': self.env.context.get('default_res_id'),
    #         'default_res_model': self.env.context.get('default_res_model'),
    #         'default_name': self.summary or self.res_name,
    #         'default_description': self.note and tools.html2plaintext(self.note).strip() or '',
    #         'default_activity_ids': [(6, 0, self.ids)],
    #     }
    #     return action
    #
    # @api.multi
    # def action_close_dialog(self):
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # # def action_feedback(self, feedback=False):
    # #     events = self.mapped('calendar_event_id')
    # #     res = super(MailActivity, self).action_feedback(feedback)
    # #     if feedback:
    # #         for event in events:
    # #             description = event.description
    # #             description = '%s\n%s%s' % (description or '', _("Feedback: "), feedback)
    # #             event.write({'description': description})
    # #     return res
    #
    # def unlink_w_meeting(self):
    #     events = self.mapped('calendar_event_id')
    #     res = self.unlink()
    #     events.unlink()
    #     return res

# def get_default(self):
        # if self.env.context.get("name", False):
        # return self._fields['res_name'].get_values(self.env)
        # a =0
    #     return self.env.context.get("res_name")
    #
    #     # return False
    #
    # names = fields.Selection(get_default, string="Name", required=True)

    # context = dict(self._context or {})
    # context['tracking_numbers'] = []

    # # partner_id = fields.Char()
    # partner_id_account=fields.Char()
    # @api.model
    # def default_get(self, fields):
    #     partner_id = fields.Char(
    #         'Document Name', compute='_compute_res_name', store=True,
    #         help="Display name of the related document.", readonly=True)
    #     name=fields.One2Many('mail.activity')
    # # @api.depends('crm_lead', 'partner_id')
    # def _compute_res_name(self):
    #     partner_id = self.env[crm_lead].browse(activity.partner_id)

    # @api.model
    # def default_get(self):
    # #
    # #     selfpartner_id = fields.Many2one(
    # #     'res.partner',
    # #     default=lambda self: self.env.user,
    # #     index=True, required=True)
    #     self.partner_id_account = self.env['crm.lead'].browse(id)
    #         # search([('id','=',self.id)])
    #
    #     # print("Partner_Id_account = ",partner_id_account)
    #     print("Self Partner_Id_account = ",self.partner_id_account)

    # name = fields.Selection([], string="Is existing project ?")
    # name = fields.Char()
    # value = fields.Integer()
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100