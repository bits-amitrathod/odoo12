
from odoo import models, fields, api, _


class CustomerContract(models.Model):
    _inherit = "res.partner"

    def _default_contract_id(self):
        contract_id = self.env['contract.contract'].search([('code', '=', 'cap')])
        return contract_id or False

    contract = fields.Many2one('contract.contract', string="Contract")


class Contract(models.Model):
    _name = 'contract.contract'
    _description = "Contract"

    name = fields.Char(string="Contract", required=True)
    code = fields.Char(string=" ", readonly="1", store=True)

    @api.model
    def create(self, val):

        name_val = val['name']
        if name_val:
            if len(name_val) >= 3:
                val['code'] = name_val[0:3]
            else:
                val['code'] = name_val

        record = super(Contract, self).create(val)
        return record

    @api.multi
    def write(self, val):

        name_val = val['name']
        if name_val:
            if len(name_val) >= 3:
                val['code'] = name_val[0:3]
            else:
                val['code'] = name_val

        record = super(Contract, self).write(val)
        return record


