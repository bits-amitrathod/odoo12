from odoo import fields, models, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    x_scac = fields.Char('SCAC')
