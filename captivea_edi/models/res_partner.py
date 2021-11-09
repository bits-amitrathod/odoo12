from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = ['res.partner']

    x_edi_accounting_id = fields.Char('Accounting ID')
    x_edi_store_number = fields.Char('Store number')
    x_edi_flag = fields.Boolean('EDI Flag')
    edi_855 = fields.Boolean('Send EDI 855')
    edi_856 = fields.Boolean('Send EDI 856')
    edi_810 = fields.Boolean('Send EDI 810')
    edi_vendor_number = fields.Char('Customer Number')
    x_edi_ship_to_type = fields.Selection([('DC', 'Warehouse Number'), ('SN', 'Store Number')], string='Ship To Type')
    remit_to = fields.Char('Remit To')
    x_billtoid = fields.Char("Bill To")
    x_storeid = fields.Char("Store ID")
    x_vendorid = fields.Char("Vendor ID")

    @api.model
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        if res.parent_id.x_edi_flag and res.type == 'delivery':
            res.edi_855 = res.edi_856 = True
        if res.parent_id.x_edi_flag and res.type == 'invoice':
            res.edi_810 = True
        return res


    @api.constrains('edi_810', 'edi_856', 'edi_855')
    def edi_flags_validate(self):
        if self.parent_id and self.parent_id.x_edi_flag:
            if not self.edi_810 and not self.edi_855 and not self.edi_856:
                raise ValidationError(_("The parent company requires at least 1 EDI document to be sent, please check "
                                        "an EDI document to send or de-activate EDI for the parent"))
