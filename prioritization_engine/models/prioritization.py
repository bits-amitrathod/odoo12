# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


# Customer Global level setting
class Customer(models.Model):
    _inherit = 'res.partner'
    prioritization = fields.Boolean("Prioritization setting" )
    sku_preconfig=fields.Char("SKU PreConfig")
    sku_postconfig = fields.Char("SKU PostConfig")
    prioritization_ids = fields.One2many('prioritization_engine.prioritization', 'customer_id')
    sps_sku = fields.Char("SPS SKU", readonly=False)
    min_threshold = fields.Integer("Product Min Threshold", readonly=False)
    max_threshold = fields.Integer("Product Max Threshold", readonly=False)
    priority = fields.Integer("Product Priority", readonly=False)
    cooling_period = fields.Integer("Cooling Period in days", readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?", readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours", readonly=False)
    expiration_tolerance = fields.Integer("Expiration Tolerance in Months", readonly=False)

    partial_ordering = fields.Boolean("Allow Partial Ordering?", readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?", readonly=False)
    order_ids = fields.One2many('sale.order', 'partner_id')
    gl_account=fields.Char("GL Account")
    on_hold= fields.Boolean("On Hold")
    is_broker=fields.Boolean("Is a Broker?")
    carrier_info=fields.Char("Carrier Info")
    carrier_acc_no = fields.Char("Carrier Account No")
    quickbook_id=fields.Char("Quickbook Id")
    having_carrier = fields.Boolean("Having Carrier?")
    notification_email=fields.Char("Notification Email")
    preferred_method=fields.Selection([
       ('mail', 'Mail'),
       ('email', 'E Mail'),
       ('both', 'E Mail & Mail ')], string='Preferred Invoice Delivery Method')
    shipping_terms = fields.Selection([
        ('1', 'Prepaid & Billed'),
        ('2', 'Prepaid'),
        (3,'Freight Collect')], string='Shipping Terms')

    @api.model
    def create(self, vals):
        self.on_hold_changes(vals)
        return super(Customer, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(Customer, self).write(vals)
        self.on_hold_changes(vals)
        return res

    def on_hold_changes(self, vals):
        for child_id in self.child_ids:
            print(child_id.on_hold);
            child_id.write({'on_hold':self.on_hold});
            print(child_id.on_hold)

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




class ProductTemplate(models.Model):
    _inherit = 'product.template'
    location = fields.Char("Location")
    premium = fields.Boolean("Premium")
    sku_code = fields.Char('SKU / Catalog No')
    manufacturer_pref = fields.Char(string='Manuf. Catalog No')


class NotificationSetting(models.Model):
    _inherit = 'res.partner'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
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
    _inherits = {'product.product':'product_id'}
    #sps_sku = fields.Char("SPS SKU",readonly=False)
    min_threshold = fields.Integer("Min Threshold",readonly=False)
    max_threshold = fields.Integer("Max Threshold",readonly=False)
    priority = fields.Integer("Product Priority",readonly=False)
    cooling_period = fields.Integer("Cooling Period in days",readonly=False)
    auto_allocate = fields.Boolean("Allow Auto Allocation?",readonly=False)
    length_of_hold = fields.Integer("Length Of Hold in hours",readonly=False)
    expiration_tolerance = fields.Integer("Expiration Tolerance in months",readonly=False)
    partial_ordering = fields.Boolean("Allow Partial Ordering?",readonly=False)
    partial_UOM = fields.Boolean("Allow Partial UOM?",readonly=False)
    length_of_holding = fields.Integer("Length Of Holding",readonly=False)
    customer_id = fields.Many2one('res.partner', string='GlobalPrioritization',required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', string='Product',required=True, ondelete="cascade")
    sales_channel = fields.Selection([('1','Manual'),('2','Prioritization Engine')], String="Sales Channel",readonly=False)# get team id = sales channel like 3 = Manual, 4 = Prioritization Engine

    _sql_constraints = [
        ('prioritization_engine_company_uniq', 'unique(customer_id,product_id)', 'Product must be unique for customer!!!!'),
    ]


class PrioritizationTransient(models.TransientModel):
    _name = 'prioritization.transient'
    min_threshold = fields.Integer("Min Threshold", readonly=False)
    max_threshold = fields.Integer("Max Threshold", readonly=False)
    priority = fields.Integer("Priority")
    cooling_period = fields.Integer("Cooling Period in days")
    auto_allocate = fields.Boolean("Allow Auto Allocation?")
    length_of_hold = fields.Integer("Length Of Hold in days")
    expiration_tolerance = fields.Integer("Expiration Tolerance days")
    partial_ordering = fields.Boolean("Allow Partial Ordering?")
    partial_UOM = fields.Boolean("Allow Partial UOM?")
    length_of_hold = fields.Integer("Lenght Of Holding")

    def action_confirm(self,arg):
        for selected in arg["selected_ids"]:
            record = self.env['prioritization_engine.prioritization'].search([('id', '=', selected)])[0]
            record.write({'min_threshold': self.min_threshold,'max_threshold': self.min_threshold,'priority': self.priority,'cooling_period': self.cooling_period,'auto_allocate': self.auto_allocate,
                        'expiration_tolerance': self.expiration_tolerance,'partial_ordering': self.partial_ordering,'partial_UOM': self.partial_UOM,
                        'length_of_hold': self.length_of_hold})
        return {'type': 'ir.actions.act_close_wizard_and_reload_view'}

class CustomerProductSetting:
    def __init__(self, customer_request_id, customer_id, product_id, product_priority, auto_allocate, cooling_period, length_of_hold, partial_order, expiration_tolerance, product_quantity):
        self.customer_request_id = customer_request_id
        self.customer_id = customer_id
        self.product_id = product_id
        self.product_priority = product_priority
        self.auto_allocate = auto_allocate
        self.cooling_period = cooling_period
        #self.last_purchased_date = last_purchased_date
        self.length_of_hold = length_of_hold
        self.partial_order = partial_order
        self.expiration_tolerance = expiration_tolerance
        self.required_product_quantity = product_quantity
