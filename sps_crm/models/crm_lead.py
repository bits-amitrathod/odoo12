import ast
import datetime

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo import api, fields, models, tools, SUPERUSER_ID
import base64
from random import randint
import logging

_logger = logging.getLogger(__name__)

class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'
    _description = 'Get Lost Reason'

    purchase_lost_reason_id = fields.Many2one('crm.purchase.lost.reason', 'purchase Lost Reason')

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
        index=True, required=True, tracking=15,
        default=lambda self: 'lead' if self.env['res.users'].has_group('crm.group_use_lead') else 'opportunity')

    purchase_stage_id = fields.Many2one(
        'crm.purchase.stage', string='Purchase Stage', index=True, tracking=True,
        compute='_compute_purchase_stage_id', readonly=False, store=True,
        copy=False, group_expand='_read_group_purchase_stage_ids', ondelete='restrict',
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")

    tag_purchase_ids = fields.Many2many(
        'crm.purchase.tag', string='Purchase Tags',
        help="Classify and analyze your lead/opportunity categories like: Training, Service")

    property_supplier_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
        string='Vendor Payment Terms',
        domain="[('company_id', 'in', [current_company_id, False])]",
        help="This payment term will be used instead of the default one for purchase orders and vendor bills")

    # contract_ids = fields.One2many('account.analytic.account', 'partner_id', string='Contracts', readonly=True)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
    contract = fields.Many2many('contract.contract', string="Contract", compute='_compute_contact_values')
    po_ref = fields.Many2one('purchase.order', string="PO#")

    product_list_doc = fields.Binary(string='Upload File', attachment=True)
    file_name = fields.Char("File Name")

    purchase_lost_reason = fields.Many2one(
        'crm.purchase.lost.reason', string='Purchase Lost Reason',
        index=True, ondelete='restrict', tracking=True)

    appraisal_no = fields.Char(string='Appraisal No#', compute="_default_appraisal_no1", readonly=False, store=True)

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

    #  Used to auto fetch data from contact
    @api.depends('partner_id')
    def _compute_contact_values(self):
        """ compute the new values when partner_id has changed """
        _logger.error(" Compute method Called ........")
        self.property_supplier_payment_term_id = self.partner_id.property_supplier_payment_term_id.id
        # self.payment_type = self.partner_id.payment_type
        self.contract = self.partner_id.contract

        print("Compute _compute_contact_values...............")


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

        #  Used to Send Email (Attached Doc)
        if 'product_list_doc' in vals:
            self.action_send_mail()

        # stage change with new stage: update probability and date_closed
        if vals.get('probability', 0) >= 100 or not vals.get('active', True):
            vals['date_closed'] = fields.Datetime.now()
        elif 'probability' in vals:
            vals['date_closed'] = False

        if any(field in ['active', 'stage_id', 'purchase_stage_id'] for field in vals):
            self._handle_won_lost(vals)



        write_result = super(Lead, self).write(vals)

        return write_result

    #  Here Write the Code Of email Send
    def action_send_mail(self):
        _logger.info(" Email Sending  ........")
        template = self.env.ref('sps_crm.email_to_crm').sudo()

        if self.product_list_doc:
            filename = str(self.file_name)
            if filename is not None:
                try:
                    file_extension = filename[filename.rindex('.') + 1:]
                    print('file extension : ' + file_extension)
                except Exception as e:
                    _logger.info(str(e))

            values = {'attachment_ids': [(0, 0, {'name': str(self.file_name),
                                                 'type': 'binary',
                                                 'mimetype': 'application/' + file_extension,
                                                 'store_fname': str(self.file_name),
                                                 'datas': base64.b64encode(self.product_list_doc)})],
                      'model': None, 'res_id': False}

            local_context = {'emailFrom': 'email_from', 'customerName': '', 'email': 'test@email.com',
                         'documentName': 'document_name', 'documentStatus': 'document_status', 'source': 'source',
                         'date': 'today_date', 'reason': 'reason'}
            try:
                sent_email_template= template.with_context(local_context).sudo().send_mail(SUPERUSER_ID, raise_exception=True)
                self.env['mail.mail'].sudo().browse(sent_email_template).write(values)
            except Exception as exc:
                _logger.error('Unable to connect to SMTP Server : %r', exc)
                response = {'message': 'Unable to connect to SMTP Server'}
