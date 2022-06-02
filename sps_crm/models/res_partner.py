from odoo import api,fields, models, tools
import logging

_logger = logging.getLogger(__name__)

class externalfiels(models.Model):
    _inherit = "res.partner"

    def pro_search_for_gpo(self, operator, value):
        if operator == '=':
            operator = '='
            name = self.env['partner.link.tracker'].search([('gpo', operator, value)], limit=None)
            return [('id', 'in', [a.partner_id.id for a in name])]

    def pro_search_for_purchase(self, operator, value):
        if operator == '=':
            operator = '='
            name = self.env['partner.link.tracker'].search([('purchase', operator, value)], limit=None)
            return [('id', 'in', [a.partner_id.id for a in name])]

    # link_code_ids = fields.Many2one(comodel_name='partner.link.tracker', relation='partner_id', string='Details Fields', index=True, ondelete='cascade')
    gpo = fields.Char(string="GPO", store=False, compute="_compute_details_field", search='pro_search_for_gpo')
    purchase = fields.Char("Purchasing", store=False, search='pro_search_for_purchase')
    mesh = fields.Char("Mesh", store=False)
    edomechanicals = fields.Char("Endomechanicals", store=False)
    orthopedic = fields.Char("Orthopedic", store=False)
    suture = fields.Char("Suture", store=False)
    gynecological = fields.Char("Gynecological",store=False)
    uology = fields.Char("Urology", store=False)
    edoscopy = fields.Char("GI/Endoscopy", store=False)
    ent = fields.Char("ENT", store=False)
    woundcare = fields.Char("Wound Care", store=False)
    bariatric = fields.Char("Bariatric", store=False)
    generalnotes = fields.Char("General Notes", store=False)
    facilityERP = fields.Char("Facility ERP", store=False)
    description = fields.Char("Description", store=False)

    captis = fields.Boolean("Captis 2.0 EIS", default=False, store=False)
    illucient = fields.Boolean("Illucient", default=False, store=False)
    capstone_health_aliance = fields.Boolean("Capstone Health Alliance #CAP-RB-013", default=False, store=False)
    salina_contract = fields.Boolean("Salina Contract", default=False, store=False)
    mha = fields.Boolean("MHA", default=False, store=False)
    veteran_affairs = fields.Boolean("Veteran Affairs", default=False, store=False)
    partners_co_operative = fields.Boolean("Partners Cooperative Inc.", default=False, store=False)
    magnet_group = fields.Boolean("MAGNET Group", default=False, store=False)
    fsasc = fields.Boolean("FSASC", default=False, store=False)
    uspi = fields.Boolean("USPI", default=False, store=False)
    surgery_partners = fields.Boolean("Surgery Partners", default=False, store=False)
    intalere_contract = fields.Boolean("Intalere Contract #: DH10128", default=False, store=False)
    premier = fields.Boolean("Premier (GPO)", default=False, store=False)
    email_opt_out = fields.Boolean("Email Opt Out", default=False, store=False)

    time_zone = fields.Selection([
        ('est', 'EST'),
        ('cst', 'CST'),
        ('mst', 'MST'),
        ('pst', 'PST'),
        ('ast', 'AST'),
        ('hast', 'HAST')], string='Time Zone', store=False)
    facility_type = fields.Selection([
        ('health_system_hospital', 'Health System Hospital'),
        ('surgery_center', 'Surgery Center'),
        ('purchasing_alliance', 'Purchasing Alliance'),
        ('charity', 'Charity'),
        ('broker', 'Broker'),
        ('veterinarian', 'Veterinarian'),
        ('non_surgery', 'Non-Surgery/Closed'),
        ('national account_target', 'National Account Target')], string='Facility Type', store=False)
    bed_size = fields.Integer(default=0, string="Bed Size", store=False)
    purchase_history_date = fields.Date(string="Last Purchase History", store=False)

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
            else:
                record.gpo =''

    @api.onchange('gpo','purchase_history_date','bed_size','facility_type','time_zone','purchase','edomechanicals','orthopedic','suture','gynecological','uology','edoscopy','ent','woundcare','bariatric','generalnotes','facilityERP','description','captis','illucient','capstone_health_aliance','salina_contract','mha','veteran_affairs','partners_co_operative','magnet_group','fsasc','uspi','surgery_partners','intalere_contract','premier','email_opt_out')
    def _onchange_fields_save(self):
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
            'purchase_history_date': self.purchase_history_date,
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
        ('health_system_hospital', 'Health System Hospital'),
        ('surgery_center', 'Surgery Center'),
        ('purchasing_alliance', 'Purchasing Alliance'),
        ('charity', 'Charity'),
        ('broker', 'Broker'),
        ('veterinarian', 'Veterinarian'),
        ('non_surgery', 'Non-Surgery/Closed'),
        ('national account_target', 'National Account Target')],string='Facility Type')
    bed_size = fields.Integer(default=0, string="Bed Size")
    purchase_history_date = fields.Date(string="Last Purchase History")