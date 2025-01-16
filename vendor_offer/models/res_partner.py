from odoo import models, fields, api, _


class CustomerACQManager(models.Model):
    _inherit = 'res.partner'

    acq_manager = fields.Many2one('res.users', string="ACQ Manager", domain="[('active', '=', True)"""
                                                                            ",('share','=',False)]")

    acq_customer_success = fields.Many2one('res.users', string="ACQ CS" , tracking=True , domain="['&',['active','=',True],['share','=',False]]")

    vendor_email = fields.Char(string="Vendor Email", tracking=True)