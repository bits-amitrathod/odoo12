from odoo import api,fields, models, tools
from odoo.osv import expression
import re
from odoo.osv.expression import get_unaccent_wrapper
import logging

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = "res.partner"

    acq_opportunity_count = fields.Integer("ACQ Opportunity", compute='_compute_acq_opportunity_count')

    def _compute_acq_opportunity_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        opportunity_data = self.env['crm.lead'].read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('type', '=', 'purchase_opportunity')],
            fields=['partner_id'], groupby=['partner_id']
        )

        self.acq_opportunity_count = 0
        for group in opportunity_data:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.acq_opportunity_count += group['partner_id_count']
                partner = partner.parent_id

    def _compute_opportunity_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        opportunity_data = self.env['crm.lead'].read_group(
            domain=[('partner_id', 'in', all_partners.ids), ('type', '=', 'opportunity')],
            fields=['partner_id'], groupby=['partner_id']
        )

        self.opportunity_count = 0
        for group in opportunity_data:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.opportunity_count += group['partner_id_count']
                partner = partner.parent_id


    def pro_search_for_gpo(self, operator, value):
        return self.generic_char_search(operator, value, 'gpo')

    def pro_search_for_purchase(self, operator, value):
        return self.generic_char_search(operator, value, 'purchase')

    def pro_search_for_mesh(self, operator, value):
        return self.generic_char_search(operator, value, 'mesh')

    def pro_search_for_edomechanicals(self, operator, value):
        return self.generic_char_search(operator, value, 'edomechanicals')

    def pro_search_for_orthopedic(self, operator, value):
        return self.generic_char_search(operator, value, 'orthopedic')

    def pro_search_for_suture(self, operator, value):
        return self.generic_char_search(operator, value, 'suture')

    def pro_search_for_gynecological(self, operator, value):
        return self.generic_char_search(operator, value, 'gynecological')

    def pro_search_for_uology(self, operator, value):
        return self.generic_char_search(operator, value, 'uology')

    def pro_search_for_edoscopy(self, operator, value):
        return self.generic_char_search(operator, value, 'edoscopy')

    def pro_search_for_ent(self, operator, value):
        return self.generic_char_search(operator, value, 'ent')

    def pro_search_for_woundcare(self, operator, value):
        return self.generic_char_search(operator, value, 'woundcare')

    def pro_search_for_bariatric(self, operator, value):
        return self.generic_char_search(operator, value, 'bariatric')

    def pro_search_for_generalnotes(self, operator, value):
        return self.generic_char_search(operator, value, 'generalnotes')

    def pro_search_for_facilityERP(self, operator, value):
        return self.generic_char_search(operator, value, 'facilityERP')

    def pro_search_for_description(self, operator, value):
        return self.generic_char_search(operator, value, 'description')

    def pro_search_for_captis(self, operator, value):
        return self.generic_char_search(operator, value, 'captis')

    def pro_search_for_illucient(self, operator, value):
        return self.generic_char_search(operator, value, 'illucient')

    def pro_search_for_capstone_health_aliance(self, operator, value):
        return self.generic_char_search(operator, value, 'capstone_health_aliance')

    def pro_search_for_salina_contract(self, operator, value):
        return self.generic_char_search(operator, value, 'salina_contract')

    def pro_search_for_mha(self, operator, value):
        return self.generic_char_search(operator, value, 'mha')

    def pro_search_for_veteran_affairs(self, operator, value):
        return self.generic_char_search(operator, value, 'veteran_affairs')

    def pro_search_for_partners_co_operative(self, operator, value):
        return self.generic_char_search(operator, value, 'partners_co_operative')

    def pro_search_for_magnet_group(self, operator, value):
        return self.generic_char_search(operator, value, 'magnet_group')

    def pro_search_for_fsasc(self, operator, value):
        return self.generic_char_search(operator, value, 'fsasc')

    def pro_search_for_uspi(self, operator, value):
        return self.generic_char_search(operator, value, 'uspi')

    def pro_search_for_surgery_partners(self, operator, value):
        return self.generic_char_search(operator, value, 'surgery_partners')

    def pro_search_for_intalere_contract(self, operator, value):
        return self.generic_char_search(operator, value, 'intalere_contract')

    def pro_search_for_premier(self, operator, value):
        return self.generic_char_search(operator, value, 'premier')

    def pro_search_for_email_opt_out(self, operator, value):
        return self.generic_char_search(operator, value, 'email_opt_out')

    def pro_search_for_ordering_day(self, operator, value):
        return self.generic_char_search(operator, value, 'ordering_day1')

    def pro_search_for_fiscal_year_end(self, operator, value):
        return self.generic_char_search(operator, value, 'fiscal_year_end')

    def pro_search_for_time_zone(self, operator, value):
        return self.generic_char_search(operator, value, 'time_zone')

    # def pro_search_for_facility_type(self, operator, value):
    #     return self.generic_char_search(operator, value, 'facility_type')

    def pro_search_for_bed_size(self, operator, value):
        return self.generic_char_search(operator, value, 'bed_size')

    def pro_search_for_purchase_history_date(self, operator, value):
        return self.generic_char_search(operator, value, 'purchase_history_date')

    def pro_search_for_top_subspecialties(self, operator, value):
        return self.generic_char_search(operator, value, 'top_subspecialties1')

    def pro_search_for_acq_account(self, operator, value):
        return self.generic_char_search(operator, value, 'acq_account')

    def pro_search_for_sales_account(self, operator, value):
        return self.generic_char_search(operator, value, 'sales_account')

    def pro_search_for_competitors_id(self, operator, value):
        return self.generic_char_search(operator, value, 'competitors_id')

    def pro_search_for_status_id(self, operator, value):
        return self.generic_char_search(operator, value, 'status_id')

    #  SaleForce_ac Custom Search Imp (Many One Search)
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        self = self.with_user(name_get_uid or self.env.uid)
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(['display_name'])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get('res_partner_search_mode')
        if (name or order_by_rank) and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else 'res_partner'
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            query = """SELECT res_partner.id
                            FROM {from_str}
                         {where} ({email} {operator} {percent}
                              OR {display_name} {operator} {percent}
                              OR {reference} {operator} {percent}
                              OR {vat} {operator} {percent}
                              OR {saleforce_ac} {operator} {percent}
                              )
                              -- don't panic, trust postgres bitmap
                        ORDER BY {fields} {display_name} {operator} {percent} desc,
                                 {display_name}
                       """.format(from_str=from_str,
                                  fields=fields,
                                  where=where_str,
                                  operator=operator,
                                  email=unaccent('res_partner.email'),
                                  display_name=unaccent('res_partner.display_name'),
                                  reference=unaccent('res_partner.ref'),
                                  percent=unaccent('%s'),
                                  vat=unaccent('res_partner.vat'),
                                  saleforce_ac=unaccent('res_partner.saleforce_ac'))

            where_clause_params += [search_name] * 4  # for email / display_name, reference
            where_clause_params += [re.sub('[^a-zA-Z0-9\-\.]+', '', search_name) or None]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            return [row[0] for row in self.env.cr.fetchall()]

        return super(Partner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    def generic_char_search(self, operator, value, field):
        partner_link = self.env['partner.link.tracker']
        if operator in ['=', '!=', 'like', 'ilike', 'not ilike', 'not like','>=','<=','<','>']:
            record = partner_link.search([(field, operator, value)], limit=None)
            return [('id', 'in', [a.partner_id.id for a in record])]
        else:
            return expression.FALSE_DOMAIN


    # link_code_ids = fields.Many2one(comodel_name='partner.link.tracker', relation='partner_id', string='Details Fields', index=True, ondelete='cascade')
    gpo = fields.Char(string="GPO", store=False, compute="_compute_details_field", search='pro_search_for_gpo', readonly=False)
    purchase = fields.Char("Purchasing", store=False, search='pro_search_for_purchase')
    mesh = fields.Char("Mesh", store=False, search='pro_search_for_mesh')
    edomechanicals = fields.Char("Endomechanicals", store=False, search='pro_search_for_edomechanicals')
    orthopedic = fields.Char("Orthopedic", store=False, search='pro_search_for_orthopedic')
    suture = fields.Char("Suture", store=False, search='pro_search_for_suture')
    gynecological = fields.Char("Gynecological",store=False, search='pro_search_for_gynecological')
    uology = fields.Char("Urology", store=False, search='pro_search_for_uology')
    edoscopy = fields.Char("GI/Endoscopy", store=False, search='pro_search_for_edoscopy')
    ent = fields.Char("ENT", store=False, search='pro_search_for_ent')
    woundcare = fields.Char("Wound Care", store=False, search='pro_search_for_woundcare')
    bariatric = fields.Char("Bariatric", store=False, search='pro_search_for_bariatric')
    generalnotes = fields.Text("General Notes", store=False, search='pro_search_for_generalnotes')
    facilityERP = fields.Char("Facility ERP", store=False, search='pro_search_for_facilityERP')
    description = fields.Text("Description", store=False, search='pro_search_for_description')

    captis = fields.Boolean("Captis 2.0 EIS", default=False, store=False, search='pro_search_for_captis')
    illucient = fields.Boolean("Illucient", default=False, store=False, search='pro_search_for_illucient')
    capstone_health_aliance = fields.Boolean("Capstone Health Alliance #CAP-RB-013", default=False, store=False, search='pro_search_for_capstone_health_aliance')
    salina_contract = fields.Boolean("Salina Contract", default=False, store=False, search='pro_search_for_salina_contract')
    mha = fields.Boolean("MHA", default=False, store=False, search='pro_search_for_mha')
    veteran_affairs = fields.Boolean("Veteran Affairs", default=False, store=False, search='pro_search_for_veteran_affairs')
    partners_co_operative = fields.Boolean("Partners Cooperative Inc.", default=False, store=False, search='pro_search_for_partners_co_operative')
    magnet_group = fields.Boolean("MAGNET Group", default=False, store=False, search='pro_search_for_magnet_group')
    fsasc = fields.Boolean("FSASC", default=False, store=False, search='pro_search_for_fsasc')
    uspi = fields.Boolean("USPI", default=False, store=False, search='pro_search_for_uspi')
    surgery_partners = fields.Boolean("Surgery Partners", default=False, store=False, search='pro_search_for_surgery_partners')
    intalere_contract = fields.Boolean("Intalere Contract #: DH10128", default=False, store=False, search='pro_search_for_intalere_contract')
    premier = fields.Boolean("Premier (GPO)", default=False, store=False, search='pro_search_for_premier')
    email_opt_out = fields.Boolean("Email Opt Out", default=False, store=False, search='pro_search_for_email_opt_out')
    ordering_day1 = fields.Many2many('day.tag', string='Ordering Day',store=False, search='pro_search_for_ordering_day')
    fiscal_year_end = fields.Selection([
        ('jan', 'January'),
        ('feb', 'February'),
        ('mar', 'March'),
        ('apr', 'April'),
        ('may', 'May'),
        ('jun', 'June'),
        ('jul', 'July'),
        ('aug', 'August'),
        ('sep', 'September'),
        ('oct', 'October'),
        ('nov', 'November'),
        ('dec', 'December')], string='Fiscal Year End', store=False, search='pro_search_for_fiscal_year_end')
    last_modify_by = fields.Many2one(comodel_name='res.partner', String='Last Modified By', store=False)
    created_by = fields.Many2one(comodel_name='res.partner', String='Created By', store=False)
    time_zone = fields.Selection([
        ('est', 'EST'),
        ('cst', 'CST'),
        ('mst', 'MST'),
        ('pst', 'PST'),
        ('ast', 'AST'),
        ('hast', 'HAST')], string='Time Zone', store=False, search='pro_search_for_time_zone')
    facility_type = fields.Selection([
        ('health_system', 'Health System'),
        ('hospital', 'Hospital'),
        ('surgery_center', 'Surgery Center'),
        ('purchasing_alliance', 'Purchasing Alliance'),
        ('charity', 'Charity'),
        ('broker', 'Broker'),
        ('veterinarian', 'Veterinarian'),
        ('non_surgery', 'Non-Surgery/Closed'),
        ('wholesale','Wholesale'),
        ('reseller', 'Reseller'),
        ('national account_target', 'National Account Target')], string='Facility Type', store=False)
    bed_size = fields.Integer(default=0, string="Bed Size", store=False, search='pro_search_for_bed_size')
    purchase_history_date = fields.Datetime(string="Last Purchase History", store=False, search='pro_search_for_purchase_history_date')

    top_subspecialties1 = fields.Many2many('specialties.tag', string='Top Subspecialties', store=False, search='pro_search_for_top_subspecialties')

    acq_account = fields.Boolean("ACQ Account", default=False, store=False, search='pro_search_for_acq_account')
    sales_account = fields.Boolean("Sales Account", default=False, store=False, search='pro_search_for_sales_account')
    competitors_id = fields.Many2many('competitors.tag', string=' Competitors', store=False, search='pro_search_for_competitors_id')
    status_id = fields.Many2many('status.tag', string='Status', store=False, search='pro_search_for_status_id', compute="_compute_details_status_field", readonly=False)
    acc_cust_parent = fields.Many2one('res.partner', string='Parent Account', store=False,
                                      domain=[('is_company', '=', True)])
    sales_activity_notes = fields.Html("Sales Activity Notes", store=False)
    acq_activity_notes = fields.Html("Acquisition Activity Notes", store=False)


    def _compute_details_field(self):
        for record in self:
            partner_link = self.env['partner.link.tracker'].search([('partner_id', '=', record.id)], limit=1)
            if partner_link:
                record.gpo = partner_link.gpo
                record.purchase = partner_link.purchase
                record.mesh = partner_link.mesh
                record.edomechanicals = partner_link.edomechanicals
                record.orthopedic = partner_link.orthopedic
                record.suture = partner_link.suture
                record.gynecological = partner_link.gynecological
                record.uology = partner_link.uology
                record.edoscopy = partner_link.edoscopy
                record.ent = partner_link.ent
                record.woundcare = partner_link.woundcare
                record.generalnotes = partner_link.generalnotes
                record.bariatric = partner_link.bariatric
                record.facilityERP = partner_link.facilityERP
                record.description = partner_link.description
                record.captis = partner_link.captis
                record.illucient = partner_link.illucient
                record.capstone_health_aliance = partner_link.capstone_health_aliance
                record.salina_contract = partner_link.salina_contract
                record.mha = partner_link.mha
                record.veteran_affairs = partner_link.veteran_affairs
                record.partners_co_operative = partner_link.partners_co_operative
                record.magnet_group = partner_link.magnet_group
                record.fsasc = partner_link.fsasc
                record.uspi = partner_link.uspi
                record.surgery_partners = partner_link.surgery_partners
                record.premier = partner_link.premier
                record.email_opt_out = partner_link.email_opt_out
                record.intalere_contract = partner_link.intalere_contract
                record.time_zone = partner_link.time_zone
                record.facility_type = partner_link.facility_type
                record.bed_size = partner_link.bed_size
                record.purchase_history_date = partner_link.purchase_history_date
                record.ordering_day1 = partner_link.ordering_day1
                record.fiscal_year_end = partner_link.fiscal_year_end
                record.last_modify_by = partner_link.last_modify_by
                record.top_subspecialties1 = partner_link.top_subspecialties1
                record.created_by = partner_link.created_by
                record.acq_account = partner_link.acq_account
                record.sales_account = partner_link.sales_account
                record.competitors_id = partner_link.competitors_id
                record.status_id = partner_link.status_id
                record.acc_cust_parent = partner_link.acc_cust_parent
                record.sales_activity_notes = partner_link.sales_activity_notes
                record.acq_activity_notes = partner_link.acq_activity_notes
            else:
                record.gpo =''

    @api.onchange('gpo','acc_cust_parent','status_id','acq_account','sales_account','competitors_id','created_by',
                  'top_subspecialties1','last_modify_by','fiscal_year_end','purchase_history_date','ordering_day1','mesh'
        ,'purchase_history_date','bed_size','facility_type','time_zone','purchase','edomechanicals','orthopedic',
                  'suture','gynecological','uology','edoscopy','ent','woundcare','bariatric','generalnotes',
                  'facilityERP','description','captis','illucient','capstone_health_aliance','salina_contract',
                  'mha','veteran_affairs','partners_co_operative','magnet_group','fsasc','uspi','surgery_partners',
                  'intalere_contract','premier','email_opt_out','acq_activity_notes','sales_activity_notes')
    def _onchange_fields_save(self):
        if len(self.ids):
            partner_id = self.ids[0]
            partner_link = self.env['partner.link.tracker']
            link_partner_record = partner_link.search([('partner_id', '=', partner_id)], limit=1)
            vals = {
                'partner_id': partner_id,'purchase': self.purchase,
                'edomechanicals': self.edomechanicals,'orthopedic': self.orthopedic,
                'suture': self.suture,'gynecological': self.gynecological,
                'uology': self.uology,'edoscopy': self.edoscopy,
                'ent': self.ent,'woundcare': self.woundcare,
                'bariatric': self.bariatric,'generalnotes': self.generalnotes,
                'facilityERP': self.facilityERP,'description': self.description,
                'captis': self.captis,'illucient': self.illucient,
                'capstone_health_aliance': self.capstone_health_aliance,
                'salina_contract': self.salina_contract,'mha': self.mha,
                'veteran_affairs': self.veteran_affairs,'partners_co_operative': self.partners_co_operative,
                'magnet_group': self.magnet_group,'fsasc': self.fsasc,
                'uspi': self.uspi,'surgery_partners': self.surgery_partners,
                'intalere_contract': self.intalere_contract,'premier': self.premier,
                'email_opt_out': self.email_opt_out,'facility_type': self.facility_type,
                'time_zone': self.time_zone,'bed_size': self.bed_size,
                'purchase_history_date': self.purchase_history_date,'mesh': self.mesh,
                'ordering_day1': self.ordering_day1.ids, 'fiscal_year_end': self.fiscal_year_end,
                'last_modify_by': self.last_modify_by, 'top_subspecialties1': self.top_subspecialties1.ids,
                'created_by': self.created_by, 'gpo': self.gpo,
                'acq_account': self.acq_account, 'sales_account': self.sales_account,
                'competitors_id': self.competitors_id.ids, 'status_id': self.status_id.ids,
                'acc_cust_parent': self.acc_cust_parent.id,
                'sales_activity_notes': self.sales_activity_notes,
                'acq_activity_notes': self.acq_activity_notes

            }
            link_partner_record.update(vals) if link_partner_record else partner_link.create(vals)

    def _compute_details_status_field(self):
        for record in self:
            partner_link = self.env['partner.link.tracker'].search([('partner_id', '=', record.id)], limit=1)
            if partner_link:
                record.status_id = partner_link.status_id
            else:
                record.status_id = record.status_id

    @api.onchange('status_id')
    def _onchange_fields_status_save(self):
        if len(self.ids):
            partner_id = self.ids[0]
            partner_link = self.env['partner.link.tracker']
            link_partner_record = partner_link.search([('partner_id', '=', partner_id)], limit=1)
            vals = {'status_id': self.status_id.ids
            }
            link_partner_record.update(vals) if link_partner_record else partner_link.create(vals)

    # THis method used to handle ACQ Oppo Button on Click
    def action_view_acq_opportunity(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        action = self.env['ir.actions.act_window']._for_xml_id('sps_crm.crm_purchase_lead_action_pipeline')
        if self.is_company:
            action['domain'] = [('partner_id.commercial_partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        else:
            action['domain'] = [('partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        return action

    def action_view_account_hierarchy(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        action = self.env['ir.actions.act_window']._for_xml_id('sps_crm.action_account_hierarchy_report')
        # if self.is_company:
        #     action['domain'] = [('partner_id.commercial_partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        # else:
        #     action['domain'] = [('partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        return action

    def action_self_hierarchy_popup(self):
        '''
                This function returns an action that displays the opportunities from partner.
                '''
        action = self.env['ir.actions.act_window']._for_xml_id('sps_crm.action_account_hierarchy_report_self')
        # if self.is_company:
        #     action['domain'] = [('partner_id.commercial_partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        # else:
        #     action['domain'] = [('partner_id.id', '=', self.id), ('type', '=', 'purchase_opportunity')]
        return action

    def action_view_activity_list_popup(self):

        act_list = self.env['mail.activity'].search([('res_id', '=', self.id), ('active', 'in', [True, False])])
        view_id = self.env.ref('sps_crm.sh_mail_activity_view_tree_popup12').id
        form_view_id = self.env.ref('sh_activities_management.sh_mail_activity_view_form').id
        return {
            'name': "Activity List",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', act_list.ids), ('active', 'in', [True, False])],
            'res_model': 'mail.activity',
            'target': 'new',
            'views': [(view_id, 'tree'), (form_view_id, 'form')]
        }

    def action_view_opportunity(self):
        '''
        This function returns an action that displays the opportunities from partner.
        '''
        action = self.env['ir.actions.act_window']._for_xml_id('crm.crm_lead_opportunities')
        if self.is_company:
            action['domain'] = [('partner_id.commercial_partner_id.id', '=', self.id), ('type', '=', 'opportunity')]
        else:
            action['domain'] = [('partner_id.id', '=', self.id), ('type', '=', 'opportunity')]
        return action

class PartnerLinkTracker(models.Model):
    _name = "partner.link.tracker"
    _description = "Customer Fields Tracker"
    # _rec_name = 'link_iid'


    # link_id = fields.Many2one('res.partner', 'Link', required=True, ondelete='cascade')
    partner_id = fields.Many2one(comodel_name='res.partner', String='Entry')

    gpo = fields.Char(string="GPO")
    purchase = fields.Char("Purchasing")
    mesh = fields.Char("Mesh")
    edomechanicals = fields.Char("Endomechanicals")
    orthopedic = fields.Char("Orthopedic")
    suture = fields.Char("Suture")
    gynecological = fields.Char("Gynecological")
    uology = fields.Char("Urology")
    edoscopy = fields.Char("GI/Endoscopy")
    ent = fields.Char("ENT")
    woundcare = fields.Char("Wound Care")
    bariatric = fields.Char("Bariatric")
    generalnotes = fields.Text("General Notes")
    facilityERP = fields.Char("Facility ERP")
    description = fields.Text("Description")

    captis = fields.Boolean("Captis 2.0 EIS", default=False)
    illucient = fields.Boolean("Illucient", default=False)
    capstone_health_aliance = fields.Boolean("Capstone Health Alliance #CAP-RB-013", default=False)
    salina_contract = fields.Boolean("Salina Contract", default=False)
    mha = fields.Boolean("MHA", default=False)
    veteran_affairs = fields.Boolean("Veteran Affairs", default=False)
    partners_co_operative = fields.Boolean("Partners Cooperative Inc.", default=False)
    magnet_group = fields.Boolean("MAGNET Group", default=False)
    fsasc = fields.Boolean("FSASC", default=False)
    uspi = fields.Boolean("USPI", default=False)
    surgery_partners = fields.Boolean("Surgery Partners", default=False)
    intalere_contract = fields.Boolean("Intalere Contract #: DH10128", default=False)
    premier = fields.Boolean("Premier (GPO)", default=False)
    email_opt_out = fields.Boolean("Email Opt Out", default=False)

    time_zone = fields.Selection([
        ('est', 'EST'),
        ('cst', 'CST'),
        ('mst', 'MST'),
        ('pst', 'PST'),
        ('ast', 'AST'),
        ('hast', 'HAST')], string='Time Zone')
    facility_type = fields.Selection([
        ('health_system', 'Health System'),
        ('hospital','Hospital'),
        ('surgery_center', 'Surgery Center'),
        ('purchasing_alliance', 'Purchasing Alliance'),
        ('charity', 'Charity'),
        ('broker', 'Broker'),
        ('veterinarian', 'Veterinarian'),
        ('non_surgery', 'Non-Surgery/Closed'),
        ('wholesale','Wholesale'),
        ('reseller', 'Reseller'),
        ('national account_target', 'National Account Target')],string='Facility Type')
    bed_size = fields.Integer(default=0, string="Bed Size")
    purchase_history_date = fields.Datetime(string="Last Purchase History")
    ordering_day1 = fields.Many2many('day.tag',string='Ordering Day')

    fiscal_year_end = fields.Selection([
        ('jan', 'January'),
        ('feb', 'February'),
        ('mar', 'March'),
        ('apr', 'April'),
        ('may', 'May'),
        ('jun', 'June'),
        ('jul', 'July'),
        ('aug', 'August'),
        ('sep', 'September'),
        ('oct', 'October'),
        ('nov', 'November'),
        ('dec', 'December')],string='Fiscal Year End')

    last_modify_by = fields.Many2one(comodel_name='res.partner', String='Last Modified By')
    created_by = fields.Many2one(comodel_name='res.partner', String='Created By')

    top_subspecialties1 = fields.Many2many('specialties.tag', string='Top Subspecialties')
    acq_account = fields.Boolean("ACQ Accoun", default=False)
    sales_account = fields.Boolean("Sales Account", default=False)
    competitors_id = fields.Many2many('competitors.tag', string='Competitors')
    status_id = fields.Many2many('status.tag', string='Status')
    acc_cust_parent = fields.Many2one('res.partner', string='Parent Account',domain=[('is_company', '=', True)])
    sales_activity_notes = fields.Html("Sales Activity Notes")
    acq_activity_notes = fields.Html("Acquisition Activity Notes")
