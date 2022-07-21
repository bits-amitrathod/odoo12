from odoo import models, fields, api, modules, exceptions, _


class MailActivityNotesCustom(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'

    sales_activity_notes = fields.Html("Sales Activity Notes", store=False, compute="_compute_act_note_field",
                                       readonly=False)
    acq_activity_notes = fields.Html("Acquisition Activity Notes", store=False, compute="_compute_act_note_field",
                                     readonly=False)

    def _compute_act_note_field(self):
        for record in self:
            if record.res_model == 'res.partner':
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=', record.res_id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

    @api.onchange('acq_activity_notes', 'sales_activity_notes')
    def onchange_notes_fields(self):
        for record in self:
            if record.res_model == 'res.partner':
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=', record.res_id)], limit=1)
                if partner_link:
                    partner_link.sales_activity_notes = record.sales_activity_notes
                    partner_link.acq_activity_notes = record.acq_activity_notes

    @api.onchange('res_id')
    def onchange_contact(self):
        for record in self:
            if record.res_model == 'res.partner':
                partner_link = self.env['partner.link.tracker'].search([('partner_id', '=', record.res_id)], limit=1)
                if partner_link:
                    record.sales_activity_notes = partner_link.sales_activity_notes
                    record.acq_activity_notes = partner_link.acq_activity_notes

