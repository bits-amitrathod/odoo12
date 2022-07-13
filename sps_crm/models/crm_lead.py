import ast
import datetime

from odoo import api, fields, models, exceptions, _
from odoo.tools.safe_eval import safe_eval
from odoo import api, fields, models, tools, SUPERUSER_ID
import base64
from random import randint
import logging
import pathlib
from odoo.exceptions import ValidationError,UserError

_logger = logging.getLogger(__name__)

class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'
    _description = 'Get Lost Reason'

    purchase_lost_reason_id = fields.Many2one('crm.purchase.lost.reason', 'Lost Reason')

    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        if self.lost_reason_id:
            return leads.action_set_lost(lost_reason=self.lost_reason_id.id)
        else:
            return leads.action_set_lost(purchase_lost_reason=self.purchase_lost_reason_id.id)

class Lead(models.Model):
    _inherit = 'crm.lead'

    type = fields.Selection([
        ('lead', 'Lead'), ('opportunity', 'Opportunity'), ('purchase_opportunity', 'Purchase Opportunity')],
        index=True, required=True,
        default=lambda self: 'lead' if self.env['res.users'].has_group('crm.group_use_lead') else 'opportunity')

    purchase_stage_id = fields.Many2one(
        'crm.purchase.stage', string='Stage', index=True,
        compute='_compute_purchase_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_purchase_stage_ids', ondelete='restrict',
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")

    tag_purchase_ids = fields.Many2many(
        'crm.purchase.tag', string='Tags',
        help="Classify and analyze your lead/opportunity categories like: Training, Service")

    property_supplier_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
        string='Vendor Payment Terms',
        domain="[('company_id', 'in', [current_company_id, False])]",
        help="This payment term will be used instead of the default one for purchase orders and vendor bills")

    # contract_ids = fields.One2many('account.analytic.account', 'partner_id', string='Contracts', readonly=True)
    payment_type = fields.Selection([('cash', 'Cash'), ('credit', 'Credit'), ('cashcredit', 'Cash/Credit')], string='Payment Type')
    contract = fields.Many2many('contract.contract', string="Contract")
    competitors = fields.Many2many('competitors.tag', string="Competitors")
    po_ref = fields.Many2one('purchase.order', string="PO#")

    product_list_doc = fields.Many2many('ir.attachment', string='Upload File', attachment=True)
    # file_name = fields.Char("File Name")

    purchase_lost_reason = fields.Many2one(
        'crm.purchase.lost.reason', string='Lost Reason',
        index=True, ondelete='restrict')

    appraisal_no = fields.Char(string='Appraisal No#', compute="_default_appraisal_no1", readonly=False, store=True)

    facility_tpcd = fields.Selection(string='Facility Type',
                                     selection=[('health_sys', 'Health System'),
                                                ('hospital', 'Hospital'),
                                                ('surgery_cen', 'Surgery Center'),
                                                ('pur_alli', 'Purchasing Alliance'),
                                                ('charity', 'Charity'),
                                                ('broker', 'Broker'),
                                                ('veterinarian', 'Veterinarian'),
                                                ('closed', 'Non-Surgery/Closed'),
                                                ('wholesale', 'Wholesale'),
                                                ('national_acc', 'National Account Target')])

    opportunity_type = fields.Selection(string='Opportunity Type',
                                     selection=[('product_acq', 'Product Acquisition'),
                                                ('eq_acq', 'EQ Acquisition'),
                                                ('wholesale_acq', 'Wholesale Acquisition'),
                                                ('product_sale', 'Product Sale'),
                                                ('eq_sale', 'EQ Sale'),
                                                ('eq_repair', 'EQ Repair'),
                                                ('national_act_cont', 'National Account Contract'),
                                                ('ka_expansion', 'KA Expansion')])

    new_customer = fields.Boolean("New Customer", default=False)
    arrival_date = fields.Datetime(string="Arrival Date")
    reason_list = fields.Selection(string='Reason for List',
                                        selection=[('conversion', 'Conversion'),
                                                   ('departure', 'Dr. Departure'),
                                                   ('inventory_level', 'Inventory/PAR Levels'),
                                                   ('short_dates', 'Short Dates'),
                                                   ('stopped_procedure', 'Stopped Procedure'),
                                                   ('facility_closure', 'Facility Closure'),
                                                   ('other', 'Other')])

    acq_priority = fields.Selection(string='Priority',
                                   selection=[('p1', 'P1'),
                                              ('p2_single_code', 'P2 Single Code'),
                                              ('p2_contract', 'P2 Contract'),
                                              ('p2', 'P2'),
                                              ('p3', 'P3')])


    @api.onchange('appraisal_no')
    def _default_appraisal_no1(self):
        for lead in self:
            if (lead.appraisal_no == False):
                while True:
                    number_str = 'AP' + str(randint(111111, 999999))
                    query_str = 'SELECT count(*) FROM crm_lead WHERE appraisal_no LIKE %s'
                    self.env.cr.execute(query_str,[number_str])
                    if 0 == self._cr.fetchone()[0]:
                        lead.appraisal_no = number_str
                        break
            else:
                query_str = 'SELECT count(*) FROM crm_lead WHERE appraisal_no LIKE %s'
                self.env.cr.execute(query_str, [lead.appraisal_no])
                if 0 != self._cr.fetchone()[0]:
                    raise ValidationError(_('Appraisal No# Already Exist'))

    @api.onchange('po_ref')
    def _default_ref_po(self):
        self.arrival_date = self.po_ref.arrival_date_grp if self.po_ref else self.arrival_date

    # Need To More Dev
    @api.constrains('product_list_doc')
    def _check_docs_ids_mimetype(self):
        required_extensions_list = ['.xlsx', '.pdf']
        for doc in self:
            file_name_list = [d.name for d in doc.product_list_doc]
        extensions_list = [pathlib.Path(f).suffix for f in file_name_list]
        if not set(extensions_list).issubset(required_extensions_list):
            raise ValidationError(_('Uploaded file does not seem to be a valid \n Required Extensions  :-' + str(required_extensions_list)))

    def _purchase_stage_find(self, team_id=False, domain=None, order='sequence'):
        """ Determine the stage of the current lead with its teams, the given domain and the given team_id
            :param team_id
            :param domain : base search domain for stage
            :returns crm.stage recordset
        """
        # collect all team_ids by adding given one, and the ones related to the current leads
        team_ids = set()
        if team_id:
            team_ids.add(team_id)
        for lead in self:
            if lead.team_id:
                team_ids.add(lead.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['crm.purchase.stage'].search(search_domain, order=order, limit=1)

    @api.depends('team_id', 'type')
    def _compute_purchase_stage_id(self):
        for lead in self:
            if not lead.purchase_stage_id and lead.type == "purchase_opportunity":
                lead.purchase_stage_id = lead._purchase_stage_find(domain=[('fold', '=', False)]).id

    @api.depends('team_id', 'type')
    def _compute_stage_id(self):
        for lead in self:
            if not lead.stage_id and lead.type == "opportunity":
                lead.stage_id = lead._stage_find(domain=[('fold', '=', False)]).id

    @api.model
    def _read_group_purchase_stage_ids(self, stages, domain, order):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends(lambda self: ['tag_ids', 'stage_id', 'team_id', 'purchase_stage_id'] + self._pls_get_safe_fields())
    def _compute_probabilities(self):
        lead_probabilities = self._pls_get_naive_bayes_probabilities()
        for lead in self:
            if lead.id in lead_probabilities:
                was_automated = lead.active and lead.is_automated_probability
                lead.automated_probability = lead_probabilities[lead.id]
                if was_automated:
                    lead.probability = lead.automated_probability

    #  Used to auto fetch data from contact
    @api.onchange('partner_id')
    def _compute_contact_values(self):
        """ compute the new values when partner_id has changed """
        _logger.error(" Compute method Called ........")
        obj = self.env['partner.link.tracker'].search([('partner_id', '=', self.partner_id.id)], limit=1).competitors_id
        self.competitors = obj.ids if obj else obj
        self.property_supplier_payment_term_id = self.partner_id.property_supplier_payment_term_id.id
        # self.payment_type = self.partner_id.payment_type
        self.contract = self.partner_id.contract
        self.facility_tpcd = self.partner_id.facility_tpcd

    #     self.env['partner.link.tracker'].search([('partner_id', '=', self.partner_id.id)],limit=1).competitors_id

    def action_purchase_set_won(self):
        """ Won semantic: probability = 100 (active untouched) """
        self.action_unarchive()
        # group the leads by team_id, in order to write once by values couple (each write leads to frequency increment)
        leads_by_won_stage = {}
        for lead in self:
            stage_id = lead._purchase_stage_find(domain=[('is_won', '=', True)])
            if stage_id in leads_by_won_stage:
                leads_by_won_stage[stage_id] |= lead
            else:
                leads_by_won_stage[stage_id] = lead
        for won_stage_id, leads in leads_by_won_stage.items():
            leads.write({'purchase_stage_id': won_stage_id.id, 'probability': 100})
        return True

    #  Won Button Action
    def action_purchase_set_won_rainbowman(self):
        self.ensure_one()
        self.action_purchase_set_won()

        message = self._get_rainbowman_message()
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/web/image/%s/%s/image_1024' % (self.team_id.user_id._name, self.team_id.user_id.id) if self.team_id.user_id.image_1024 else '/web/static/src/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        return True

    def _handle_won_lost(self, vals):
        """ This method handle the state changes :
        - To lost : We need to increment corresponding lost count in scoring frequency table
        - To won : We need to increment corresponding won count in scoring frequency table
        - From lost to Won : We need to decrement corresponding lost count + increment corresponding won count
        in scoring frequency table.
        - From won to lost : We need to decrement corresponding won count + increment corresponding lost count
        in scoring frequency table."""
        Lead = self.env['crm.lead']
        leads_reach_won = Lead
        leads_leave_won = Lead
        leads_reach_lost = Lead
        leads_leave_lost = Lead
        won_stage_ids = self.env['crm.stage'].search([('is_won', '=', True)]).ids
        won_purchase_stage_ids = self.env['crm.purchase.stage'].search([('is_won', '=', True)]).ids
        for lead in self:
            if 'stage_id' in vals:
                if vals['stage_id'] in won_stage_ids:
                    if lead.probability == 0:
                        leads_leave_lost |= lead
                    leads_reach_won |= lead
                elif lead.stage_id.id in won_stage_ids and lead.active:  # a lead can be lost at won_stage
                    leads_leave_won |= lead

            if 'purchase_stage_id' in vals:
                if vals['purchase_stage_id'] in won_purchase_stage_ids:
                    if lead.probability == 0:
                        leads_leave_lost |= lead
                    leads_reach_won |= lead
                elif lead.purchase_stage_id.id in won_purchase_stage_ids and lead.active:  # a lead can be lost at won_stage
                    leads_leave_won |= lead

            if 'active' in vals:
                if not vals['active'] and lead.active:  # archive lead
                    if lead.stage_id.id in won_stage_ids and lead not in leads_leave_won:
                        leads_leave_won |= lead
                    if lead.purchase_stage_id.id in won_purchase_stage_ids and lead not in leads_leave_won:
                        leads_leave_won |= lead
                    leads_reach_lost |= lead
                elif vals['active'] and not lead.active:  # restore lead
                    leads_leave_lost |= lead

        leads_reach_won._pls_increment_frequencies(to_state='won')
        leads_leave_won._pls_increment_frequencies(from_state='won')
        leads_reach_lost._pls_increment_frequencies(to_state='lost')
        leads_leave_lost._pls_increment_frequencies(from_state='lost')

    def write(self, vals):
        if vals.get('website'):
            vals['website'] = self.env['res.partner']._clean_website(vals['website'])

        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            stage_id = self.env['crm.stage'].browse(vals['stage_id'])
            if stage_id.is_won:
                vals.update({'probability': 100, 'automated_probability': 100})

        # stage change: update date_last_stage_update
        if 'purchase_stage_id' in vals:
            stage_id = self.env['crm.purchase.stage'].browse(vals['purchase_stage_id'])
            if stage_id.is_won:
                vals.update({'probability': 100, 'automated_probability': 100})

        # stage change with new stage: update probability and date_closed
        if vals.get('probability', 0) >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif 'probability' in vals:
            vals['date_closed'] = False

        if any(field in ['active', 'stage_id', 'purchase_stage_id'] for field in vals):
            self._handle_won_lost(vals)



        write_result = super(Lead, self).write(vals)

        #  Used to Send Email (Attached Doc)
        #  Right Place to Send Email bcz of All uploaded file Operation Completed before this step
        if 'product_list_doc' in vals:
            self.action_send_mail()

        return write_result

    #  Here Write the Code Of email Send
    def action_send_mail(self):
        _logger.info(" Email Sending  ........")
        template = self.env.ref('sps_crm.email_to_crm').sudo()
        if self.product_list_doc:
            values = {'attachment_ids':self.product_list_doc,
                          'model': None, 'res_id': False}
            local_context = {'rep': self.partner_id.acq_manager.name, 'unq_ac': self.partner_id.saleforce_ac,
                             'facility_type': self.facility_tpcd, 'contracts': self.contract,
                             'history': '', 'competitors':  self.competitors,
                             'payment_type': self.payment_type, 'payment_terms': self.property_supplier_payment_term_id.name,
                             'additional_notes': 'Notes'}
            try:
                sent_email_template= template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
                self.env['mail.mail'].sudo().browse(sent_email_template).write(values)
            except Exception as exc:
                _logger.error('Unable to connect to SMTP Server : %r', exc)
                response = {'message': 'Unable to connect to SMTP Server'}

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        for lead in self:
            if lead.partner_id.phone and lead._get_partner_phone_update():
                lead.phone = lead.partner_id.phone
                lead.property_supplier_payment_term_id = lead.partner_id.property_supplier_payment_term_id
                # lead.payment_type = lead.partner_id.payment_type
                obj = self.env['partner.link.tracker'].search([('partner_id', '=', lead.partner_id.id)],
                                                           limit=1).competitors_id
                lead.contract = lead.partner_id.contract
                lead.competitors = obj
                lead.facility_tpcd = lead.partner_id.facility_tpcd
                # lead.arrival_date = lead.po_ref.arrival_date_grp if lead.po_ref else lead.arrival_date

class MailActivity1(models.Model):
    """ Inherited Mail Acitvity to add custom View for Purchase Oppo"""
    _inherit = 'mail.activity'

    def action_view_activity(self):
        self.ensure_one()
        view_id_purchase = self.env.ref(
            'sps_crm.crm_lead_view_form_purchase').id

        try:
            model = self.env[self.res_model].browse(
                self.res_id).check_access_rule('read')

            if self.res_model == "crm.lead":
                res = self.env['crm.lead'].sudo().search([('id', '=', self.res_id)], limit=1)
                if res.type == 'purchase_opportunity':
                    return {
                        'name': 'Origin Activity',
                        'view_mode': 'form',
                        'res_model': self.res_model,
                        'views': [(view_id_purchase, 'form')],
                        'res_id': self.res_id,
                        'type': 'ir.actions.act_window',
                        'target': 'current',
                    }

            return{
                'name': 'Origin Activity',
                'res_model': self.res_model,
                'res_id': self.res_id,
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        except exceptions.AccessError:
            raise exceptions.UserError(
                _('Assigned user %s has no access to the document and is not able to handle this activity.') %
                self.env.user.display_name)

    @api.depends('date_deadline')
    def _compute_state(self):
        for record in self.filtered(lambda activity: activity.date_deadline):
            tz = record.user_id.sudo().tz
            date_deadline = record.date_deadline
            record.state = self._compute_state_from_date(date_deadline, tz)
            record.sh_state = record.state
