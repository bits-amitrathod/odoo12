from odoo import api, fields, models, _
from datetime import datetime

from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.tools.misc import clean_context, format_date, OrderedSet
import logging
_logger = logging.getLogger(__name__)
PICKING_TYPE_ID = 1

class StockMoveExtension(models.Model):
    _inherit = "stock.move"

    def _get_lot_name(self,id):
        if isinstance(id, int):
            lot_id = self.env['stock.move.line'].search([('id', '=', id)])
            if lot_id:
             return lot_id.lot_name
        return False

    def write(self, vals):
        # Handle the write on the initial demand by updating the reserved quantity and logging
        # messages according to the state of the stock.move records.
        # customize code start
        global serialNumber
        global serialNumberExDate

        temp_var = 0
        for this in self:
            lotNumbers = []
            product_tmpl = self.env['product.template'].search([('id', '=', int(this.product_id.product_tmpl_id))])
            params = self.env['ir.config_parameter'].sudo()
            group_stock_production_lot = params.get_param('inventory_extension.group_stock_production_lot')

            product_expiry = self.env['ir.module.module'].sudo().search([('name', '=', 'product_expiry')])
            module_product_expiry = True if product_expiry.state == 'installed' else False
            show_lots_m2o = this.has_tracking != 'none' and (
                    this.picking_type_id.use_existing_lots or this.state == 'done' or this.origin_returned_move_id.id),  # able to create lots, whatever the value of ` use_create_lots`.
            show_lots_text = this.has_tracking != 'none' and this.picking_type_id.use_create_lots and not this.picking_type_id.use_existing_lots and this.state != 'done' and not this.origin_returned_move_id.id,
            if show_lots_m2o[0] or show_lots_text[0]:
                try:
                    serialNumber = False
                    serialNumberExDate = False
                    for ml in vals.get('move_line_ids', {}):
                        if isinstance(ml[2], dict):
                            if ('lot_id' in ml[2] and not ml[2].get('lot_id')):
                                if (not 'lot_name' in ml[2] and not self._get_lot_name(ml[1])):
                                    serialNumber = True
                                elif ('lot_name' in ml[2] and not ml[2].get('lot_name')):
                                    serialNumber = True
                                elif (module_product_expiry and not 'lot_expired_date' in ml[
                                    2] and not self._get_lot_name(ml[1])):
                                    lotNumbers.append(
                                        ml[2].get('lot_name') if ml[2].get('lot_name') else self._get_lot_name(ml[1]))
                                    serialNumberExDate = True
                                elif (module_product_expiry and 'lot_expired_date' in ml[2] and not ml[2].get(
                                        'lot_expired_date')):
                                    lotNumbers.append(
                                        ml[2].get('lot_name') if ml[2].get('lot_name') else self._get_lot_name(ml[1]))
                                    serialNumberExDate = True
                                if (module_product_expiry and not serialNumberExDate and (
                                        not 'lot_expired_date' in ml[2] or not ml[2].get('lot_expired_date'))):
                                    lotNumbers.append(
                                        ml[2].get('lot_name') if ml[2].get('lot_name') else self._get_lot_name(ml[1]))
                                    serialNumberExDate = True
                except KeyError:
                    print("key error pass:")
                    pass;
                if serialNumber and serialNumberExDate:
                    raise UserError(_('Lot/Serial Number and Expiration Date is required.'))
                elif serialNumberExDate:
                    msg = "Expiration Date for Lot/Serial Numbers " if len(
                        lotNumbers) > 1 else "Expiration Date for Lot/Serial Number "
                    row = 0;
                    for number in lotNumbers:
                        if row > 0:
                            msg = msg + "," + number
                        else:
                            msg = msg + number
                        row = row + 1
                    raise UserError(_(msg + " " + "is required."))
                elif serialNumber:
                    raise UserError(_('Lot/Serial Number is required.'))
        # customize code end
        receipt_moves_to_reassign = self.env['stock.move']
        if 'product_uom_qty' in vals:
            for move in self.filtered(lambda m: m.state not in ('done', 'draft') and m.picking_id):
                if vals['product_uom_qty'] != move.product_uom_qty:
                    self.env['stock.move.line']._log_message(move.picking_id, move, 'stock.track_move_template', vals)
            if self.env.context.get('do_not_unreserve') is None:
                move_to_unreserve = self.filtered(
                    lambda m: m.state not in ['draft', 'done', 'cancel'] and m.reserved_availability > vals.get('product_uom_qty'))
                move_to_unreserve._do_unreserve()
                (self - move_to_unreserve).filtered(lambda m: m.state == 'assigned').write({'state': 'partially_available'})
                # When editing the initial demand, directly run again action assign on receipt moves.
                receipt_moves_to_reassign |= move_to_unreserve.filtered(lambda m: m.location_id.usage == 'supplier')
                receipt_moves_to_reassign |= (self - move_to_unreserve).filtered(lambda m: m.location_id.usage == 'supplier' and m.state in ('partially_available', 'assigned'))
        if 'date_deadline' in vals:
            self._set_date_deadline(vals.get('date_deadline'))
        #  By Pass The Creation Code and Added new Code to Create Record
        if 'move_line_ids' in vals:
            if self.picking_type_id.id == PICKING_TYPE_ID:
                result_list = [item for item in vals['move_line_ids'] if '0' in str(item[0])]
                vals['move_line_ids'] = [item for item in vals['move_line_ids'] if '0' not in str(item[0])]
                stock_loc = self.env['stock.location'].sudo()
                stock_lot = self.env['stock.production.lot'].sudo()
                id_list = self.move_line_ids.ids
                for rl in result_list:
                    result = self._update_reserved_quantity(rl[2].get('qty_done'), rl[2].get('qty_done'), stock_loc.browse(rl[2].get('location_id')), lot_id=stock_lot.browse(rl[2].get('lot_id'))if stock_lot.browse(rl[2].get('lot_id')).exists() else None, package_id=None, owner_id=None, strict=True)
                    if result:
                        non_matching_elements = list(set(id_list) ^ set(self.move_line_ids.ids))
                        for item in self.move_line_ids.filtered(lambda x: x.id in non_matching_elements):
                            item.state = 'assigned'
                            item.qty_done = item.product_uom_qty
                        self.state = 'assigned'

                # update Reserved Qty According to done Qty
                for item in vals['move_line_ids']:
                    if item[0] == 1 and 'qty_done' in item[2]:
                        item[2]['product_uom_qty'] = item[2]['qty_done']

        res = super(StockMoveExtension, self).write(vals)
        if receipt_moves_to_reassign:
            receipt_moves_to_reassign._action_assign()

        # if self.product_uom_qty < self.quantity_done:
        #     raise ValidationError('Reserved Quantity Is More then Demanded Quantity')
        return res

    def getParent(self, saleOrder):
        return saleOrder.partner_id.parent_id if saleOrder.partner_id.parent_id else saleOrder.partner_id

    def action_show_details(self):
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()

        picking_type_id = self.picking_type_id or self.picking_id.picking_type_id

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        if self.picking_type_id.name in ['Pick'] and self.getParent(self.picking_id[0].sale_id).picking_warn in ["block"]:
            return {
                    'name': _("Warning for %s") % self.getParent(self.picking_id[0].sale_id).name,
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'warning.popup.wizard',
                    'type': 'ir.actions.act_window',
                    'context': {'default_picking_warn_msg': self.getParent(self.picking_id[0].sale_id).picking_warn_msg},
                    'target': 'new', }
        else:
            return {
                'name': _('Detailed Operations'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.move',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': dict(
                    self.env.context,
                    show_owner=self.picking_type_id.code != 'incoming',
                    show_lots_m2o=self.has_tracking != 'none' and (
                                picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),
                    # able to create lots, whatever the value of ` use_create_lots`.
                    show_lots_text=self.has_tracking != 'none' and picking_type_id.use_create_lots and not picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                    show_source_location=self.picking_type_id.code != 'incoming',
                    show_destination_location=self.picking_type_id.code != 'outgoing',
                    show_package=not self.location_id.usage == 'supplier',
                    show_reserved_quantity=self.state != 'done' and not self.picking_id.immediate_transfer and self.picking_type_id.code != 'incoming',
                    show_lot_id_column=self.has_tracking != 'none' and (
                                picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id) and self.picking_type_id.code != 'incoming',
                    do_not_show_lot_id_column=self.has_tracking != 'none' and (
                                picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id) and self.picking_type_id.code == 'incoming'
                ),
            }

    def update_qty_done(self):
        moves_to_unreserve = OrderedSet()
        for move in self:
            if move.state == 'cancel' or (move.state == 'done' and move.scrapped):
                # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                # We may have done move in an open picking in a scrap scenario.
                continue
            elif move.state == 'done':
                raise UserError(_("You cannot unreserve a stock move that has been set to 'Done'."))
            moves_to_unreserve.add(move.id)
        moves_to_unreserve = self.env['stock.move'].browse(moves_to_unreserve)

        ml_to_update = OrderedSet()
        moves_not_to_recompute = OrderedSet()
        for ml in moves_to_unreserve.move_line_ids:
            if ml.qty_done:
                ml_to_update.add(ml.id)
        ml_to_update = self.env['stock.move.line'].browse(ml_to_update)
        ml_to_update.write({'qty_done': 0})

        moves_not_to_recompute = self.env['stock.move'].browse(moves_not_to_recompute)

        # `write` on `stock.move.line` doesn't call `_recompute_state` (unlike to `unlink`),
        # so it must be called for each move where no move line has been deleted.
        (moves_to_unreserve - moves_not_to_recompute)._recompute_state()
        return True

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    short = fields.Html(string="Short")
    extra = fields.Html(string="Extra")
    short_date = fields.Html(string="Notes")

    def do_unreserve(self):
        self.move_lines.update_qty_done()
        super(StockPicking, self).do_unreserve()

class StockMoveLineInh(models.Model):
    _inherit = "stock.move.line"
    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        res = {}
        # Check if move_id exists and has the correct picking type
        if self.move_id and self.move_id.picking_type_id.id == PICKING_TYPE_ID:
            demanded_qty = self.move_id.product_uom_qty
            total_done_qty = sum(lm.qty_done for lm in self.move_id.move_line_ids if lm.qty_done > 0 and not lm.id.ref)

            # Warn if done quantity exceeds demanded quantity
            if demanded_qty and demanded_qty < total_done_qty:
                message = _('Done Qty(%s) is More than Demanded Qty(%s)') % (total_done_qty, demanded_qty)
                res['warning'] = {'title': _('Warning'), 'message': message}

        # Warn if qty_done exceeds available quantity in the lot
        if self.lot_id and self.move_id.picking_type_id[0].id == PICKING_TYPE_ID:
            old_obj = self._origin.lot_id if self._origin and self._origin.lot_id else None
            new_obj = self.lot_id
            flag = True if old_obj and old_obj.id != new_obj.id else False

            available_qty_for_sale = self.env['stock.quant'].sudo()._get_available_quantity \
                (self.product_id, self.picking_location_id, lot_id=self.lot_id, package_id=None,
                 owner_id=None, strict=False, allow_negative=False)
            available_qty = available_qty_for_sale if flag else (available_qty_for_sale + self.product_uom_qty)
            if self.qty_done > available_qty:
                message = _('Your requested Done Qty(%s) is Not Available in Lot(%s)') % (self.qty_done, self.lot_id.name)
                res['warning'] = {'title': _('Warning'), 'message': message}
                self.qty_done = available_qty

        return res