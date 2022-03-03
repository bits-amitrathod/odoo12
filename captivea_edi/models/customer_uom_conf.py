from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CustomerUoMConf(models.Model):
    _name = 'customer.uom.conf'
    _description = 'Customer UoM Configuration'

    name = fields.Char(copy=False)
    line_ids = fields.One2many('customer.uom.conf.line', 'conf_id')

    @api.constrains('name')
    def validate_lines(self):
        for conf in self:
            duplicate_line = self.env['customer.uom.conf'].search(
                [('id', '!=', conf.id), ('name', '=ilike', conf.name)])
            if duplicate_line:
                raise ValidationError(
                    _('You are trying to create duplicate configuration. Please create configuration with different name.'))


class CustomerUoMConfLine(models.Model):
    _name = 'customer.uom.conf.line'
    _description = 'Customer UoM Configuration Lines'

    conf_id = fields.Many2one('customer.uom.conf')
    edi_uom = fields.Char(string='EDI UoM')
    uom_id = fields.Many2one('uom.uom', string='SPS UoM')

    @api.constrains('edi_uom', 'uom_id')
    def validate_lines(self):
        for line in self:
            duplicate_line = self.env['customer.uom.conf.line'].search(
                [('id', '!=', line.id), ('conf_id', '=', line.conf_id.id),
                 ('edi_uom', '=ilike', line.edi_uom), ('uom_id', '=', line.uom_id.id)])
            if duplicate_line:
                raise ValidationError(
                    _('You are trying to create duplicate line. Please create lines with different values.'))
