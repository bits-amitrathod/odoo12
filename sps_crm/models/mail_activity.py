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

    @api.onchange('acq_activity_notes', 'sales_activity_notes')
    def onchange_notes_fields(self):
        for record in self:
            if record.related_partner_activity:
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
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
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=',
                                                                         record.related_partner_activity.id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

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

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(MailActivityNotesCustom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                submenu=submenu)
    #     res.res_model = 'res.partner'
    #     return res

