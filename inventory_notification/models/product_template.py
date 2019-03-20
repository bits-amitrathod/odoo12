

from odoo import api, fields, models, tools, _



class ProductTemplate(models.Model):
    _inherit = "product.template"
    notify = fields.Boolean("Can be Notify")


