
from odoo import models, api
from odoo.exceptions import UserError


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def unlink(self):
        if self.filtered(lambda line: line.state in 'done' and (line.invoice_lines or not line.is_downpayment)):
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        return models.Model.unlink(self)

