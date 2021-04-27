from odoo import api, fields, models, _
from datetime import datetime

from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
import logging

_logger = logging.getLogger(__name__)


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
        res = super(StockMoveExtension, self).write(vals)
        if receipt_moves_to_reassign:
            receipt_moves_to_reassign._action_assign()
        return res