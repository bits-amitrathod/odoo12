from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError,ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    cust_po = fields.Char("Customer PO", readonly=False)
    client_order_ref = fields.Char(string='Purchase Order#', copy=False)
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
    def _compute_show_validate(self):
        _logger.info('self %r',self)
        sale_order_list = [self.ids]
        for sale_id in sale_order_list:
            multi = self.env['stock.picking'].search([('sale_id', '=', sale_id)])
            _logger.info('**multi : %r',multi)
            if len(multi) == 1 and self.delivery_count ==1:
                self.show_validate=multi.show_validate
            elif self.delivery_count > 1:
                self.show_validate=True

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
        if len(multi) == 1 and self.delivery_count ==1:
            return multi.button_validate()
        elif self.delivery_count>1:
            raise ValidationError(_('Validate is not possible for multiple delivery please do validate one by one'))


    def action_assign(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.action_assign()


    @api.multi
    def do_unreserve(self):
        multi = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        if len(multi) >= 1:
            return multi.do_unreserve()

    @api.multi
    def action_quotation_send(self):
        print('saleorder -> action_quotation_send()')
        """
        This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    customer_request_id = fields.Many2one('sps.customer.requests', string='Request')

    def action_show_details(self):
       multi= self.env['stock.move'].search([('sale_line_id', '=', self.id)])
       if len(multi) >= 1  and self.order_id.delivery_count ==1:
           return multi.action_show_details()
       elif self.order_id.delivery_count>1:
           raise ValidationError(_('Picking is not possible for multiple delivery please do picking inside Delivery'))


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def button_validate(self):
        _logger.info("stock :stock_picking_prioritization  button_validate called.....")
        _logger.info("stock :stock_picking_prioritization parnter hold status %r :",self.partner_id)

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
        memo = fields.Char("Memo")
        shipping_terms = fields.Selection(string='Shipping Term', related='partner_id.shipping_terms', readonly=True)
        preferred_method = fields.Selection(string='Preferred Invoice Delivery Method',
                                            related='partner_id.preferred_method', readonly=True)

        '''name = fields.Char(string='Purchase Order#', index=True,
                           readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                           help='The name that will be used on account move lines')

        origin = fields.Char(string='Sale Order#',
                             help="Reference of the document that produced this invoice.",
                             readonly=True, states={'draft': [('readonly', False)]})'''
