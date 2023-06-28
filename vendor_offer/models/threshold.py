from odoo import api, fields, models

class Threshold(models.Model):
    _name = "vendor.threshold"
    _description = "vendor offer threshold"
    _rec_name = 'name'

    _sql_constraints = [
        ('exclude_threshold_in_code_uniq', 'unique (code)', 'Threshold Code should be Unique')
    ]

    name = fields.Char('Threshold Name', required=True, translate=True)
    worth = fields.Integer('Yearly Sales Worth', default=1, help="Number of yearly sales worth of inventory")
    code = fields.Char('Code', required=True)
