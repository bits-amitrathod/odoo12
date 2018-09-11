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



    def write(self, vals):
        global serialNumber;
        global serialNumberExDate;
        lotNumbers = []

        for ml in  self:
            _logger.info("template id : %r", ml.product_id.product_tmpl_id)
            product_tmpl=self.env['product.template'].search([('id', '=', int(ml.product_id.product_tmpl_id))])
            params = self.env['ir.config_parameter'].sudo()
            group_stock_production_lot = params.get_param('inventory_extension.group_stock_production_lot')
            module_product_expiry = params.get_param('inventory_extension.module_product_expiry')
            if product_tmpl.tracking =='lot' and group_stock_production_lot:
                try:
                    serialNumber = False;
                    serialNumberExDate = False;
                    for ml in vals.get('move_line_ids', {}):
                        if ('lot_id' in ml[2] and not ml[2].get('lot_id')):
                            _logger.info("lot expire date  : %r",  ('lot_expired_date' in ml[2]))
                            if (not 'lot_name' in ml[2] or not ml[2].get('lot_name')):
                                serialNumber = True
                            elif(module_product_expiry and ( not 'lot_expired_date' in ml[2] or not ml[2].get('lot_expired_date'))):
                                lotNumbers.append(ml[2].get('lot_name'))
                                serialNumberExDate = True
                            if (module_product_expiry  and not serialNumberExDate and  (not 'lot_expired_date' in ml[2] or not ml[2].get('lot_expired_date'))):
                                serialNumberExDate = True
                except KeyError:
                    print("key error pass:")
                    pass;
                if serialNumber and serialNumberExDate:
                    raise UserError(_('Lot/Serial Number and Expiration Date is required.'))
                elif serialNumberExDate:
                    msg="Expiration Date for Lot/Serial Numbers " if len(lotNumbers)>1 else "Expiration Date for Lot/Serial Number "
                    row=0;
                    for number in lotNumbers:
                        if row>0:
                         msg=msg+","+number
                        else:
                            msg = msg + number
                        row=row+1
                    raise UserError(_(msg + " "+ "is required."))
                elif serialNumber:
                    raise UserError(_('Lot/Serial Number is required.'))


        # FIXME: pim fix your crap
        receipt_moves_to_reassign = self.env['stock.move']
        if 'product_uom_qty' in vals:
            for move in self.filtered(lambda m: m.state not in ('done', 'draft') and m.picking_id):
                if vals['product_uom_qty'] != move.product_uom_qty:
                    self.env['stock.move.line']._log_message(move.picking_id, move, 'stock.track_move_template', vals)
            if self.env.context.get('do_not_unreserve') is None:
                move_to_unreserve = self.filtered(lambda m: m.state not in ['draft', 'done', 'cancel'] and m.reserved_availability > vals.get('product_uom_qty'))
                move_to_unreserve._do_unreserve()
                (self - move_to_unreserve).filtered(lambda m: m.state == 'assigned').write({'state': 'partially_available'})
                # When editing the initial demand, directly run again action assign on receipt moves.
                receipt_moves_to_reassign |= move_to_unreserve.filtered(lambda m: m.location_id.usage == 'supplier')
                receipt_moves_to_reassign |= (self - move_to_unreserve).filtered(lambda m: m.location_id.usage == 'supplier' and m.state in ('partially_available', 'assigned'))

        # TDE CLEANME: it is a gros bordel + tracking
        Picking = self.env['stock.picking']

        propagated_changes_dict = {}
        #propagation of expected date:
        propagated_date_field = False
        if vals.get('date_expected'):
            #propagate any manual change of the expected date
            propagated_date_field = 'date_expected'
        elif (vals.get('state', '') == 'done' and vals.get('date')):
            #propagate also any delta observed when setting the move as done
            propagated_date_field = 'date'

        if not self._context.get('do_not_propagate', False) and (propagated_date_field or propagated_changes_dict):
            #any propagation is (maybe) needed
            for move in self:
                if move.move_dest_ids and move.propagate:
                    if 'date_expected' in propagated_changes_dict:
                        propagated_changes_dict.pop('date_expected')
                    if propagated_date_field:
                        current_date = datetime.strptime(move.date_expected, DEFAULT_SERVER_DATETIME_FORMAT)
                        new_date = datetime.strptime(vals.get(propagated_date_field), DEFAULT_SERVER_DATETIME_FORMAT)
                        delta_days = (new_date - current_date).total_seconds() / 86400
                        if abs(delta_days) >= move.company_id.propagation_minimum_delta:
                            old_move_date = datetime.strptime(move.move_dest_ids[0].date_expected, DEFAULT_SERVER_DATETIME_FORMAT)
                            new_move_date = (old_move_date + relativedelta.relativedelta(days=delta_days or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            propagated_changes_dict['date_expected'] = new_move_date
                    #For pushed moves as well as for pulled moves, propagate by recursive call of write().
                    #Note that, for pulled moves we intentionally don't propagate on the procurement.
                    if propagated_changes_dict:
                        move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel')).write(propagated_changes_dict)
        track_pickings = not self._context.get('mail_notrack') and any(field in vals for field in ['state', 'picking_id', 'partially_available'])
        if track_pickings:
            to_track_picking_ids = set([move.picking_id.id for move in self if move.picking_id])
            if vals.get('picking_id'):
                to_track_picking_ids.add(vals['picking_id'])
            to_track_picking_ids = list(to_track_picking_ids)
            pickings = Picking.browse(to_track_picking_ids)
            initial_values = dict((picking.id, {'state': picking.state}) for picking in pickings)
        res = super(StockMoveExtension, self).write(vals)
        if track_pickings:
            pickings.message_track(pickings.fields_get(['state']), initial_values)
        if receipt_moves_to_reassign:
            receipt_moves_to_reassign._action_assign()
        return res