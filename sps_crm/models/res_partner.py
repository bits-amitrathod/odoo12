from odoo import api,fields, models, tools
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)

class externalfiels(models.Model):
    _inherit = "res.partner"

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
        return self.generic_char_search(operator, value, 'ordering_day')

    def pro_search_for_fiscal_year_end(self, operator, value):
        return self.generic_char_search(operator, value, 'fiscal_year_end')

    def pro_search_for_time_zone(self, operator, value):
        return self.generic_char_search(operator, value, 'time_zone')

    def pro_search_for_facility_type(self, operator, value):
        return self.generic_char_search(operator, value, 'facility_type')

    def pro_search_for_bed_size(self, operator, value):
        return self.generic_char_search(operator, value, 'bed_size')

    def pro_search_for_purchase_history_date(self, operator, value):
        return self.generic_char_search(operator, value, 'purchase_history_date')

    def pro_search_for_top_subspecialties(self, operator, value):
        return self.generic_char_search(operator, value, 'top_subspecialties')



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
    generalnotes = fields.Char("General Notes", store=False, search='pro_search_for_generalnotes')
    facilityERP = fields.Char("Facility ERP", store=False, search='pro_search_for_facilityERP')
    description = fields.Char("Description", store=False, search='pro_search_for_description')

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

    ordering_day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday')], string='Ordering Day',store=False, search='pro_search_for_ordering_day')
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
    last_modify = fields.Many2one(comodel_name='res.partner', String='Last Modified By', store=False)
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
        ('national account_target', 'National Account Target')], string='Facility Type', store=False, search='pro_search_for_facility_type')
    bed_size = fields.Integer(default=0, string="Bed Size", store=False, search='pro_search_for_bed_size')
    purchase_history_date = fields.Date(string="Last Purchase History", store=False, search='pro_search_for_purchase_history_date')

    top_subspecialties = fields.Selection([
        ('endoscopy', 'Endoscopy'),
        ('ent', 'ENT'),
        ('eyes', 'Eyes'),
        ('general_surgery', 'General Surgery'),
        ('gyn', 'GYN'),
        ('orthopedic', 'Orthopedic'),
        ('pain', 'Pain'),
        ('plastic_surgery', 'Plastic Surgery'),
        ('urology', 'Urology'),
        ('podiatry', 'Podiatry'),
        ('bariatrics', 'Bariatrics'),
        ('wound_care', 'Wound Care')], string='Top Subspecialties', store=False, search='pro_search_for_top_subspecialties')


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
                record.ordering_day = partner_link.ordering_day
                record.fiscal_year_end = partner_link.fiscal_year_end
                record.last_modify = partner_link.last_modify
                record.top_subspecialties = partner_link.top_subspecialties
                record.created_by = partner_link.created_by
            else:
                record.gpo =''

    @api.onchange('gpo','created_by','top_subspecialties','last_modify','fiscal_year_end','purchase_history_date','ordering_day','mesh','purchase_history_date','bed_size','facility_type','time_zone','purchase','edomechanicals','orthopedic','suture','gynecological','uology','edoscopy','ent','woundcare','bariatric','generalnotes','facilityERP','description','captis','illucient','capstone_health_aliance','salina_contract','mha','veteran_affairs','partners_co_operative','magnet_group','fsasc','uspi','surgery_partners','intalere_contract','premier','email_opt_out')
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
                'ordering_day': self.ordering_day, 'fiscal_year_end': self.fiscal_year_end,
                'last_modify': self.last_modify, 'top_subspecialties': self.top_subspecialties,
                'created_by': self.created_by, 'gpo': self.gpo

            }
            link_partner_record.update(vals) if link_partner_record else partner_link.create(vals)

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
    generalnotes = fields.Char("General Notes")
    facilityERP = fields.Char("Facility ERP")
    description = fields.Char("Description")

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
        ('national account_target', 'National Account Target')],string='Facility Type')
    bed_size = fields.Integer(default=0, string="Bed Size")
    purchase_history_date = fields.Date(string="Last Purchase History")
    ordering_day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday')],string='Ordering Day')

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

    last_modify = fields.Many2one(comodel_name='res.partner', String='Last Modified By')
    created_by = fields.Many2one(comodel_name='res.partner', String='Created By')

    top_subspecialties = fields.Selection([
        ('endoscopy', 'Endoscopy'),
        ('ent', 'ENT'),
        ('eyes', 'Eyes'),
        ('general_surgery', 'General Surgery'),
        ('gyn', 'GYN'),
        ('orthopedic', 'Orthopedic'),
        ('pain', 'Pain'),
        ('plastic_surgery', 'Plastic Surgery'),
        ('urology', 'Urology'),
        ('podiatry', 'Podiatry'),
        ('bariatrics', 'Bariatrics'),
        ('wound_care', 'Wound Care')],string='Top Subspecialties')