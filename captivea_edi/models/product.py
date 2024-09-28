from odoo import fields, models, api


class Product(models.Model):
    _inherit = 'product.template'



    edi_charge_amount = fields.Boolean(help='Select if this product needs to be included as a Charge Amount for the EDI 810')

    # edi_allowance_amount = fields.Float(string='Allowance Amount')
    edi_allowance_amount = fields.Boolean(
        help='Select if this product needs to be included as a Allowance Amount for the EDI 810')
