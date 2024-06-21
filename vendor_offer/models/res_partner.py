from odoo import models, fields, api, _


class CustomerACQManager(models.Model):
    _inherit = 'res.partner'

    acq_manager = fields.Many2one('res.users', string="ACQ Manager", domain="[('active', '=', True)"""
                                                                            ",('share','=',False)]")

    vendor_email = fields.Char(string="Vendor Email", track_visibility='onchange')