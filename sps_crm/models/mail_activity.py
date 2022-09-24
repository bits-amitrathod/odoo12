from odoo import models, fields, api, modules, exceptions, _


class MailActivityNotesCustom(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'

    sales_activity_notes = fields.Html("Sales Activity Notes", store=False, compute="_compute_act_note_field",
                                       readonly=False)
    acq_activity_notes = fields.Html("Acquisition Activity Notes", store=False, compute="_compute_act_note_field",
                                     readonly=False)

    related_partner_activity = fields.Many2one('res.partner', string="Related Partner")

    activity_priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')], string='Priority', store=True)

    reference = fields.Reference(string='Related Document',
                                 selection='_reference_models', default='res.partner,1')

    email = fields.Char(related="related_partner_activity.email", readonly=True, store=False)
    phone = fields.Char(related="related_partner_activity.phone", readonly=True, store=False)
    mobile = fields.Char(related="related_partner_activity.mobile", readonly=True, store=False)

    #date_done = fields.Date("Completed Date", index=True, readonly=False)

    # def write(self, vals):
    #     res = super().write(vals)
    #     return res

    @api.model
    def _reference_models(self):

        # models = self.env['ir.model'].sudo().search([('state', '!=', 'manual'), ('name', 'not in', model_list),
        #                                              ('name', 'not like', 'report'), ('name', 'not like', 'popup'),
        #                                              ('name', 'not like', 'Test'), ('name', 'not like', 'Tests'),
        #                                              ('name', 'not like', 'sps'), ('name', 'not like', 'prioritization'),
        #                                              ('name', 'not like', 'Tests')])

        model_list = ['Contact', 'Sales Order', 'Vendor Offer Automation', 'Lead/Opportunity']
        models = self.env['ir.model'].sudo().search([('state', '!=', 'manual'), ('name', 'in', model_list)])
        res = [(model.model, model.name)
               for model in models
               if not model.model.startswith('ir.')]
        return res


    def _compute_act_note_field(self):
        for record in self:
            # record.res_model = 'res.partner'
            # record.reference = 'res.partner,1'
            if record.related_partner_activity:
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

    @api.model
    def create(self, val):
        if val['res_model_id'] == False:
            val['res_model_id'] = self.env['ir.model'].sudo().search([('model', '=', 'res.partner')], limit=1).id
        record = super(MailActivityNotesCustom, self).create(val)
        popup_context = self.env.context.get('default_res_model')
        popup_model_id = self.env.context.get('default_res_id')
        if popup_context == 'res.partner' and popup_model_id:
            record.reference = self.env['res.partner'].search([('id', '=', popup_model_id)], limit=1)
        return record

    @api.onchange('acq_activity_notes', 'sales_activity_notes')
    def onchange_notes_fields(self):
        for record in self:
            popup_context = self.env.context.get('default_res_model')
            if popup_context == 'res.partner' and record.related_partner_activity.id is False:
                record.related_partner_activity = self.env['res.partner'].search([('id', '=', record.res_id)], limit=1)
            if record.related_partner_activity:
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    if popup_context == 'res.partner':
                        if record.sales_activity_notes :
                            partner_link.sales_activity_notes = record.sales_activity_notes
                        else:
                            record.sales_activity_notes = partner_link.sales_activity_notes

                        if record.acq_activity_notes:
                            partner_link.acq_activity_notes = record.acq_activity_notes
                        else:
                            record.acq_activity_notes = partner_link.acq_activity_notes
                    else:
                        partner_link.sales_activity_notes = record.sales_activity_notes
                        partner_link.acq_activity_notes = record.acq_activity_notes
                else:
                    self.env['partner.link.tracker'].create({'partner_id': record.related_partner_activity.id,
                                                             'sales_activity_notes': record.sales_activity_notes,
                                                             'acq_activity_notes': record.acq_activity_notes })

    @api.onchange('related_partner_activity')
    def onchange_contact(self):
        for record in self:
            if record.related_partner_activity:
                # record.res_name = record.related_partner_activity.name
                # record.res_id = record.related_partner_activity.id
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

    # Overwritten because Client Does Not want Notes overridden
    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            if self.activity_type_id.summary:
                self.summary = self.activity_type_id.summary
            self.date_deadline = self._calculate_date_deadline(self.activity_type_id)
            self.user_id = self.activity_type_id.default_user_id or self.env.user
            # if self.activity_type_id.default_description:
            #     self.note = self.activity_type_id.default_description

    # Overwritten because Client Does Not want Pop Up
    def action_done(self):
        self.state = 'done'
        self.active = False
        self.activity_done = True
        self.date_done = fields.Date.today()
        self.feedback = ''
        self._compute_state()
        messages = self.env['mail.message']
        record = self.env[self.res_model].sudo().browse(self.res_id)
        record.sudo().message_post_with_view(
            'mail.message_activity_done',
            values={
                'activity': self,
                'feedback': '',
                'display_assignee': self.user_id != self.env.user
            },
            subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
            mail_activity_type_id=self.activity_type_id.id,
        )
        messages |= record.sudo().message_ids[0]

    def action_view_activity(self):
        self.ensure_one()
        view_id = self.env.ref(
            'sh_activities_management.sh_mail_activity_view_form').id
        return {
            'name': _('Schedule an Activity'),
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(view_id, 'form')],
            'res_id': self.id,
            'type': 'ir.actions.act_window'
        }

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(MailActivityNotesCustom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                submenu=submenu)
    #     res.res_model = 'res.partner'
    #     return res

    # @api.model
    # def create(self, values):
    #     # activity = super(MailActivityNotesCustom, self).create(values)
    #     activity = super(models.Model, self).create(values)
    #     need_sudo = False
    #     try:  # in multicompany, reading the partner might break
    #         partner_id = activity.user_id.partner_id.id
    #     except exceptions.AccessError:
    #         need_sudo = True
    #         partner_id = activity.user_id.sudo().partner_id.id
    #
    #     # send a notification to assigned user; in case of manually done activity also check
    #     # target has rights on document otherwise we prevent its creation. Automated activities
    #     # are checked since they are integrated into business flows that should not crash.
    #     if activity.user_id != self.env.user:
    #         if not activity.automated:
    #             activity._check_access_assignation()
    #         # if not self.env.context.get('mail_activity_quick_update', False):
    #         #     if need_sudo:
    #         #         activity.sudo().action_notify()
    #         #     else:
    #         #         activity.action_notify()
    #
    #     self.env[activity.res_model].browse(activity.res_id).message_subscribe(partner_ids=[partner_id])
    #     if activity.date_deadline <= fields.Date.today():
    #         self.env['bus.bus'].sendone(
    #             (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #             {'type': 'activity_updated', 'activity_created': True})
    #     return activity
    #
    # def write(self, values):
    #     if values.get('user_id'):
    #         user_changes = self.filtered(lambda activity: activity.user_id.id != values.get('user_id'))
    #         pre_responsibles = user_changes.mapped('user_id.partner_id')
    #     # res = super(MailActivityNotesCustom, self).write(values)
    #     res = super(models.Model, self).write(values)
    #
    #     # if values.get('user_id'):
    #     #     if values['user_id'] != self.env.uid:
    #     #         to_check = user_changes.filtered(lambda act: not act.automated)
    #     #         to_check._check_access_assignation()
    #     #         if not self.env.context.get('mail_activity_quick_update', False):
    #     #             user_changes.action_notify()
    #     #     for activity in user_changes:
    #     #         self.env[activity.res_model].browse(activity.res_id).message_subscribe(
    #     #             partner_ids=[activity.user_id.partner_id.id])
    #     #         if activity.date_deadline <= fields.Date.today():
    #     #             self.env['bus.bus'].sendone(
    #     #                 (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #     #                 {'type': 'activity_updated', 'activity_created': True})
    #     #     for activity in user_changes:
    #     #         if activity.date_deadline <= fields.Date.today():
    #     #             for partner in pre_responsibles:
    #     #                 self.env['bus.bus'].sendone(
    #     #                     (self._cr.dbname, 'res.partner', partner.id),
    #     #                     {'type': 'activity_updated', 'activity_deleted': True})
    #     return res
    #
    # def unlink(self):
    #     pass
    #     # for activity in self:
    #     #     if activity.date_deadline <= fields.Date.today():
    #     #         self.env['bus.bus'].sendone(
    #     #             (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
    #     #             {'type': 'activity_updated', 'activity_deleted': True})
    #     # return super(MailActivityNotesCustom, self).unlink()


