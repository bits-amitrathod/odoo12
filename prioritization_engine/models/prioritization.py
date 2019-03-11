# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


# Customer Global level setting
class Customer(models.Model):
    _inherit = 'res.partner'

    prioritization = fields.Boolean("Prioritization setting")
    sku_preconfig = fields.Char("SKU PreConfig")
    sku_postconfig = fields.Char("SKU PostConfig")
    prioritization_ids = fields.One2many('prioritization_engine.prioritization', 'customer_id')
    min_threshold = fields.Integer("Product Min Threshold", readonly=False)
    max_threshold = fields.Integer("Product Max Threshold", readonly=False)
    priority = fields.Integer("Product Priority", default=-1, readonly=False, help="if Product Priority is -1 then Prioritization Engine will process only those products which are added in 'Customer Priority Configuration'.")
    cooling_period = fields.Integer("Cooling Period in days", readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?", readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours", readonly=False, default=1)
    expiration_tolerance = fields.Integer("Expiration Tolerance in Months", readonly=False)
    partial_ordering = fields.Boolean("Allow Partial Ordering?", readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?", readonly=False)
    order_ids = fields.One2many('sale.order', 'partner_id')
    gl_account = fields.One2many('gl.account', 'partner_id', string="GL Account")
    on_hold = fields.Boolean("On Hold")
    is_broker = fields.Boolean("Is a Broker?")
    carrier_info = fields.Char("Carrier Info")
    carrier_acc_no = fields.Char("Carrier Account No")
    quickbook_id = fields.Char("Quickbook Id")
    having_carrier = fields.Boolean("Having Carrier?")
    notification_email = fields.Char("Notification Email")
    saleforce_ac = fields.Char("SF A/C No#")
    is_share = fields.Boolean("Is Shared")
    sale_margine = fields.Selection([
        ('gifted', 'Gifted'),
        ('legacy', 'Legacy')], string='Sales Level')
    preferred_method = fields.Selection([
        ('mail', 'Mail'),
        ('email', 'E Mail'),
        ('both', 'E Mail & Mail ')], string='Preferred Invoice Delivery Method')
    shipping_terms = fields.Selection([
        ('1', 'Prepaid & Billed'),
        ('2', 'Prepaid'),
        ('3', 'Freight Collect')], string='Shipping Terms')
    allow_purchase = fields.Boolean("Purchase Order Method")
    is_parent = fields.Boolean("Purchase Order Method", default=True)

    @api.model
    def create(self, vals):
        self.copy_parent_date(vals)
        return super(Customer, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(Customer, self).write(vals)
        print(res)
        res2 = self.copy_parent_date(vals)
        print(res2)
        return res

    def copy_parent_date(self, vals):
        # print(self)
        # self.ensure_one()
        _logger.info("pritization engin :%r", vals)
        for ml in self:
            for child_id in ml.child_ids:
                # print(child_id.child_ids)
                child_id.write({'on_hold': ml.on_hold,
                                'is_broker': ml.is_broker,
                                'carrier_info': ml.carrier_info,
                                'carrier_acc_no': ml.carrier_acc_no,
                                'quickbook_id': ml.quickbook_id,
                                'having_carrier': ml.having_carrier,
                                'preferred_method': ml.preferred_method,
                                'shipping_terms': ml.shipping_terms,
                                'allow_purchase': ml.allow_purchase,
                                'sku_preconfig': ml.sku_preconfig,
                                'sku_postconfig': ml.sku_postconfig,
                                'is_parent': False,
                                'prioritization': ml.prioritization,
                                'prioritization_ids': ml.prioritization_ids,
                                'min_threshold': ml.min_threshold,
                                'priority': ml.priority,
                                'partial_UOM': ml.partial_UOM,
                                'partial_ordering': ml.partial_ordering,
                                'auto_allocate': ml.auto_allocate,
                                'length_of_hold': ml.length_of_hold,
                                'expiration_tolerance': ml.expiration_tolerance,
                                'cooling_period': ml.cooling_period,
                                'max_threshold': ml.max_threshold});

    def action_view_notification(self):
        '''
        This function returns an action that display existing notification
        of given partner ids. It can be form
        view,
        '''
        action = self.env.ref('prioritization_engine.action_notification_setting').read()[0]
        action['views'] = [(self.env.ref('prioritization_engine.view_notification_setting_form').id, 'form')]
        action['view_ids'] = self.env.ref('prioritization_engine.view_notification_setting_form').id
        action['res_id'] = self.id
        return action

    def action_gl_account(self):
        action = self.env.ref('prioritization_engine.action_glaccount_setting').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_import(self):
        '''
        This function returns an action that display existing notification
        of given partner ids. It can be form
        view,
        '''
        action = self.env.ref('stock.product_template_action_product').read()[0]
        action['views'] = [(self.env.ref('product.product_template_tree_view').id, 'tree')]
        action['view_ids'] = self.env.ref('product.product_template_tree_view').id
        action['res_id'] = self.id
        return action

    def action_import_template(self):
        tree_view_id = self.env.ref('customer-requests.view_tree_documents_normal').id
        return {
            'type': 'ir.actions.client',
            'views': [(tree_view_id, 'form')],
            'view_mode': 'form',
            'tag': 'importtemplate',
            'params': [
                {'model': 'sps.customer.template', 'customer_id': self.id, 'user_type': 'customer', 'request_model':
                    'sps.customer.requests'}],
        }

    # constraint
    @api.constrains('expiration_tolerance')
    @api.one
    def _check_expiration_tolerance(self):
        expiration_tolerance = self.expiration_tolerance
        if expiration_tolerance and len(str(abs(expiration_tolerance))) > 3:
            raise ValidationError(
                _('Global Priority Configuration->Expiration Tolerance field must be less than 3 digit'))

    @api.constrains('length_of_hold')
    @api.one
    def _check_length_of_hold(self):
        if self.prioritization:
            length_of_hold = self.length_of_hold
            if length_of_hold and len(str(abs(length_of_hold))) > 5:
                raise ValidationError(
                    _('Global Priority Configuration->Length of Holding field must be less than 5 digit'))
            elif length_of_hold == 0:
                self.length_of_hold = 1
                raise ValidationError(_('Global Priority Configuration->Length of Holding field should not be 0'))

    @api.constrains('priority')
    @api.one
    def _check_priority(self):
        priority = self.priority
        if priority and len(str(abs(priority))) > 5:
            raise ValidationError(_('Global Priority Configuration->Priority field must be less than 5 digit'))

    @api.constrains('cooling_period')
    @api.one
    def _check_cooling_period(self):
        cooling_period = self.cooling_period
        if cooling_period and cooling_period >= 366:
            raise ValidationError(_('Global Priority Configuration->Cooling Period field must be less 365 days'))

    @api.constrains('max_threshold')
    @api.one
    def _check_max_threshold(self):
        max_threshold = self.max_threshold
        if max_threshold and max_threshold >= 999:
            raise ValidationError(_('Global Priority Configuration->Max Threshold field must be less 999'))
        if max_threshold and max_threshold <= self.min_threshold:
            raise ValidationError(
                _('Global Priority Configuration->Max Threshold field must be greater than Min Threshold field'))

    @api.constrains('min_threshold')
    @api.one
    def _check_min_threshold(self):
        min_threshold = self.min_threshold
        if min_threshold and min_threshold > 999:
            raise ValidationError(_('Global Priority Configuration->Min Threshold field must be less 999'))

    @api.onchange('prioritization', 'allow_purchase')
    def _check_prioritization_setting(self):
        warning = {}
        vals = {}
        if self.allow_purchase == False and self.prioritization == True:
            vals.update({'prioritization': False})
            warning = {
                'title': _('Warning'),
                'message': _('Please Select Purchase Order Method For Prioritization setting'),
            }
        return {'value': vals,'warning':warning}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_default_uom_id(self):
        return self.env["product.uom"].search([('name', 'ilike', 'each')], limit=1, order='id').id

    location = fields.Char("Location")
    premium = fields.Boolean("Premium")
    sku_code = fields.Char('SKU / Catalog No')
    manufacturer_pref = fields.Char(string='Manuf. Catalog No')
    manufacturer_uom = fields.Many2one('product.uom', 'Manufacturer Unit of Measure', default=_get_default_uom_id,
                                       required=True)


class NotificationSetting(models.Model):
    _inherit = 'res.partner'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    historic_months = fields.Integer("Last XX Historic Months")
    monday = fields.Boolean("Monday")
    tuesday = fields.Boolean("Tuesday")
    wednesday = fields.Boolean("Wednesday")
    thursday = fields.Boolean("Thursday")
    friday = fields.Boolean("Friday")
    saturday = fields.Boolean("Saturday")
    sunday = fields.Boolean("Sunday")


# Customer product level setting
class Prioritization(models.Model):
    _name = 'prioritization_engine.prioritization'
    _inherits = {'product.product': 'product_id'}
    min_threshold = fields.Integer("Min Threshold", readonly=False)
    max_threshold = fields.Integer("Max Threshold", readonly=False)
    priority = fields.Integer("Product Priority", readonly=False)
    cooling_period = fields.Integer("Cooling Period in days", readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?", readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours", readonly=False, default=1)
    expiration_tolerance = fields.Integer("Expiration Tolerance in months", readonly=False)
    partial_ordering = fields.Boolean("Allow Partial Ordering?", readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?", readonly=False)
    customer_id = fields.Many2one('res.partner', string='GlobalPrioritization', required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete="cascade")
    sales_channel = fields.Selection([('1', 'Manual'), ('2', 'Prioritization Engine')], String="Sales Channel",
                                     readonly=False)  # get team id = sales channel like 3 = Manual, 4 = Prioritization Engine

    _sql_constraints = [
        ('priority_engine_uniq', 'unique (product_id,customer_id)',
         'In Customer Priority Configuration Product Value Repeated !')
    ]

    def import_product(self, records, cust_id):
        for record in records:
            self.create({'customer_id': cust_id, 'product_id': record['id']})

    # constraint
    @api.constrains('expiration_tolerance')
    @api.one
    def _check_expiration_tolerance(self):
        expiration_tolerance = self.expiration_tolerance
        if expiration_tolerance and len(str(abs(expiration_tolerance))) > 3:
            raise ValidationError(
                _('Customer Priority Configuration->Expiration Tolerance field must be less than 3 digit'))

    @api.constrains('length_of_hold')
    @api.one
    def _check_length_of_hold(self):
        length_of_hold = self.length_of_hold
        if length_of_hold and len(str(abs(length_of_hold))) > 5:
            raise ValidationError(
                _('Customer Priority Configuration->Length of Holding field must be less than 5 digit'))
        elif length_of_hold == 0:
            raise ValidationError(_('Customer Priority Configuration->Length of Holding field should not be 0'))

    @api.constrains('priority')
    @api.one
    def _check_priority(self):
        priority = self.priority
        if priority and len(str(abs(priority))) > 5:
            raise ValidationError(_('Customer Priority Configuration->Priority field must be less than 5 digit'))

    @api.constrains('cooling_period')
    @api.one
    def _check_cooling_period(self):
        cooling_period = self.cooling_period
        if cooling_period and cooling_period >= 366:
            raise ValidationError(_('Customer Priority Configuration->Cooling Period field must be less 365 days'))

    @api.constrains('max_threshold')
    @api.one
    def _check_max_threshold(self):
        # max_threshold = self.max_threshold
        if self.max_threshold and self.max_threshold >= 999:
            raise ValidationError(_('Customer Priority Configuration->Max Threshold field must be less 999'))
        if self.min_threshold and self.max_threshold <= self.min_threshold:
            raise ValidationError(
                _('Customer Priority Configuration->Max Threshold field must be greater than Min Threshold field'))

    @api.constrains('min_threshold')
    @api.one
    def _check_min_threshold(self):
        min_threshold = self.min_threshold
        if min_threshold and min_threshold > 999:
            raise ValidationError(_('Customer Priority Configuration->Min Threshold field must be less 999'))


class PrioritizationTransient(models.TransientModel):
    _name = 'prioritization.transient'
    min_threshold = fields.Integer("Min Threshold", readonly=False)
    max_threshold = fields.Integer("Max Threshold", readonly=False)
    priority = fields.Integer("Priority")
    cooling_period = fields.Integer("Cooling Period in days")
    auto_allocate = fields.Boolean("Allow Auto Allocation?")
    length_of_hold = fields.Integer("Length Of Hold in hours")
    expiration_tolerance = fields.Integer("Expiration Tolerance in months")
    partial_ordering = fields.Boolean("Allow Partial Ordering?")
    partial_UOM = fields.Boolean("Allow Partial UOM?")

    def action_confirm(self, arg):
        for selected in arg["selected_ids"]:
            record = self.env['prioritization_engine.prioritization'].search([('id', '=', selected)])[0]
            record.write(
                {'min_threshold': self.min_threshold, 'max_threshold': self.max_threshold, 'priority': self.priority,
                 'cooling_period': self.cooling_period, 'auto_allocate': self.auto_allocate,
                 'expiration_tolerance': self.expiration_tolerance, 'partial_ordering': self.partial_ordering,
                 'partial_UOM': self.partial_UOM,
                 'length_of_hold': self.length_of_hold})
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}


class SalesChannelPrioritization(models.Model):
    _inherit = "crm.team"
    team_type = fields.Selection([('engine', 'Prioritization'), ('sales', 'Sales'), ('website', 'Website')],
                                 string='Channel Type', default='sales',
                                 required=True,
                                 help="The type of this channel, it will define the resources this channel uses.")


class StockMove(models.Model):
    _inherit = "stock.move"
    partial_UOM = fields.Boolean("Allow Partial UOM?", compute="_get_partial_UOM", readonly=True)
    default_code = fields.Char("SKU", store=False, readonly=True, related='product_id.product_tmpl_id.default_code')

    @api.multi
    def _get_partial_UOM(self):
        _logger.info('partner id : %r, product id : %r', self.partner_id.id, self.product_id.id)
        if self.partner_id and self.product_id:
            setting = self.env['sps.customer.requests'].get_settings_object(self.partner_id.id, self.product_id.id,
                                                                            None, None)
            if setting:
                if setting.partial_UOM and not setting.partial_UOM is None:
                    _logger.info('partial UOM** : %r', setting.partial_UOM)
                    self.partial_UOM = setting.partial_UOM

class GLAccount(models.Model):
    _name = "gl.account"

    _sql_constraints = [
        ('name', 'unique(name)', 'GL Account already exists'),
    ]
    name = fields.Char(string='GL Account', required=True, translate=True)
    partner_id=fields.Many2one('res.partner',string='Partner')


