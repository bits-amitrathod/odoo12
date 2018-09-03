from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    cust_po = fields.Char("Customer PO", readonly=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('engine', 'Prioritization'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('void', 'Voided'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to compute whether the validate should be shown.')
    shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
    preferred_method = fields.Selection(string='Preferred Invoice Delivery Method', related='partner_id.preferred_method', readonly=True)
    carrier_info = fields.Char("Carrier Info",related='partner_id.carrier_info',readonly=True)
    carrier_acc_no = fields.Char("Carrier Account No",related='partner_id.carrier_acc_no',readonly=True)

    @api.multi
    def action_void(self):
        return self.write({'state': 'void'})

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel','void'):
               raise UserError(
                    'You can not delete a sent quotation or a sales order! Try to cancel or void it before.')
        return models.Model.unlink(self)

    def action_validate(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.button_validate()

    def action_assign(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.action_assign()

    def _compute_show_validate(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi)>=1:
            multi._compute_show_validate()

    @api.multi
    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def action_show_details(self):
       self= self.env['stock.move'].search([('sale_line_id', '=', self.id)])
       if self.id:
           return self.action_show_details()

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        _logger.info("stock :stock_picking_prioritization  button_validate called.....")

        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_(
                'You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))
        if self.partner_id.on_hold:
            if picking_type.code == "outgoing":
                raise UserError(_(
                    'Customer is on hold. You cannot validate a transfer.'))
        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)
                    elif line.qty_done == 0:
                        raise UserError(_(
                            'You cannot validate a transfer if you have not processed any quantity for %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {'name': _('Immediate Transfer?'), 'type': 'ir.actions.act_window', 'view_type': 'form',
                'view_mode': 'form', 'res_model': 'stock.immediate.transfer', 'views': [(view.id, 'form')],
                'view_id': view.id, 'target': 'new', 'res_id': wiz.id, 'context': self.env.context, }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer', 'views': [(view.id, 'form')], 'view_id': view.id,
                'target': 'new', 'res_id': wiz.id, 'context': self.env.context, }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return

class AccountInvoice(models.Model):
        _inherit = 'account.invoice'
        expiration_date=fields.Date("Expiration Date")
        note = fields.Char("Customer Message")
        shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
        preferred_method = fields.Selection(string='Preferred Invoice Delivery Method',
                                            related='partner_id.preferred_method', readonly=True)