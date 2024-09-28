
from odoo import api, fields, models, tools, SUPERUSER_ID, _
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

class hide_state_code(models.Model):
    _inherit = 'res.country.state'

    #@api.multi
    def name_get(self):
        # super(hide_state_code,self).name_get()
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result
