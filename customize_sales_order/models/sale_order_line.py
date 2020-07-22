
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Business Development', readonly=True)

    # @api.multi
    # def unlink(self):
    #     if self.filtered(lambda line: line.state in 'done' and (line.invoice_lines or not line.is_downpayment)):
    #         raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
    #     return models.Model.unlink(self)

    @api.multi
    def unlink(self):
        if self.filtered(
                lambda line: line.state in ('sale', 'done') and (line.invoice_lines or not line.is_downpayment)):
            raise UserError(_(
                'You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        elif self.filtered(
                lambda line: line.order_id.team_id.team_type == 'engine' and
                             (line.state in ('sent', 'sale', 'done') and (line.invoice_lines or not line.is_downpayment))):
            raise UserError(_(
                'You can not remove an order line.\nYou should rather set the quantity to 0.'))

        return super(SaleOrderLineInherit, self).unlink()

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        # When modifying a one2many, _origin doesn't guarantee that its values will be the ones
        # in database. Hence, we need to explicitly read them from there.
        if self._origin:
            product_uom_qty_origin = self._origin.read(["product_uom_qty"])[0]["product_uom_qty"]
        else:
            product_uom_qty_origin = 0

        if self.state == 'sale' and self.product_id.type in ['product',
                                                             'consu'] and self.product_uom_qty < product_uom_qty_origin:
            # Do not display this warning if the new quantity is below the delivered
            # one; the `write` will raise an `UserError` anyway.
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _(
                    'You are decreasing the ordered quantity! Do not forget to manually update the delivery order if needed.'),
            }
            return {'warning': warning_mess}

        elif self.order_id.team_id.team_type == 'engine' and (self.state in ('sale', 'sent') and self.product_id.type in ['product',
                                                             'consu'] and self.product_uom_qty < product_uom_qty_origin):
            # Do not display this warning if the new quantity is below the delivered
            # one; the `write` will raise an `UserError` anyway.
            if self.product_uom_qty < self.qty_delivered:
                return {}
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _(
                    'You are decreasing the ordered quantity! Do not forget to manually update the delivery order if needed.'),
            }
            return {'warning': warning_mess}
        return {}

