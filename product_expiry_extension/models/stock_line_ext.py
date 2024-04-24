# -*- coding: utf-8 -*-
from collections import Counter
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api
from odoo.tools import OrderedSet
import logging
import datetime
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class InventoryExe(models.Model):
    _inherit = 'stock.move.line'
    lot_expired_date = fields.Datetime('Expiration Date')
    lot_use_date = fields.Datetime('Expiration Date', compute='_compute_show_lot_user_date',readOnly=True, required=True)
    lot_id_po = fields.Many2one(
        'stock.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)

    @api.onchange('lot_id_po')
    def _onchange_lot_id_po(self):
        _logger.info("check_barcode_date _onchange_lot_id_po")
        self.lot_id = self.lot_id_po

    # @api.onchange('qty_done')
    # def _onchange_qty_done(self):
    #     _logger.info("check_barcode_date qty_done")

    @api.onchange('lot_use_date')
    def _onchange_lot_use_date(self):
        _logger.info("check_barcode_date _onchange_lot_use_date")
        if self.lot_id.id and self.lot_use_date:
            values = {}
            values = self._get_updated_date(self.lot_use_date, values)
            self.env['stock.lot'].search([('id', '=', self.lot_id.id)]).write(values)

    @api.onchange('expiration_date')
    def _onchange_lot_use_date2(self):
        _logger.info("check_barcode_date _onchange_lot_use_date2")
        if self.lot_id_po.id and self.expiration_date:
            values = {}
            values = self._get_updated_date(self.expiration_date, values)
            self.env['stock.lot'].search([('id', '=', self.lot_id_po.id)]).write(values)

    def _get_updated_date(self,lot_use_date,vals):
        params = self.env['ir.config_parameter'].sudo()
        production_lot_alert_days = int(params.get_param('inventory_extension.production_lot_alert_days'))

        if production_lot_alert_days > 0:
            alert_date = datetime.datetime.strptime(str(lot_use_date), '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=production_lot_alert_days)
        else:
            alert_date = datetime.datetime.strptime(str(lot_use_date), '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=3)

        vals.update({'use_date': str(lot_use_date), 'alert_date': str(alert_date), 'expiration_date': str(lot_use_date),'removal_date': str(lot_use_date)})

        return vals

    def write(self, vals):
        _logger.info("check_barcode_date write")
        record = super(InventoryExe, self).write(vals)
        _logger.info("check_barcode_date write %s", self.env.context.get('picking_type_code'))
        if self.env.context.get('picking_type_code') and self.env.context.get('picking_type_code') == 'incoming':
            if self.lot_id.id and self.expiration_date:
                _logger.info("check_barcode_date write exp date")
                values = {}
                values = self._get_updated_date(self.expiration_date, values)
                self.env['stock.lot'].search([('id', '=', self.lot_id.id)]).write(values)
        return record

    @api.onchange('lot_name', 'lot_id','lot_expired_date')
    def _onchange_serial_number(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
                help him. This includes:
                    - automatically switch `qty_done` to 1.0
                    - warn if he has already encoded `lot_name` in another move line
                """
        _logger.info("move_line_onchange sewrial number calledd.")
        res = {}

        if self.lot_id:
            self._compute_show_lot_user_date()
        if self.product_id.tracking == 'serial':
            if not self.qty_done:
                self.qty_done = 1

            message = None
            if self.lot_name or self.lot_expired_date or self.lot_id:

                move_lines_to_check = self._get_similar_move_lines() - self
                if self.lot_name:
                    if self.lot_expired_date is False:
                        res['warning'] = {'title': _('Warning'), 'message': "expired date required"}
                        return res
                    counter = Counter(move_lines_to_check.mapped('lot_name'))
                    if counter.get(self.lot_name) and counter[self.lot_name] > 1:
                        message = _(
                            'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    elif not self.lot_id:
                        counter = self.env['stock.lot'].search_count([
                            ('company_id', '=', self.company_id.id),
                            ('product_id', '=', self.product_id.id),
                            ('name', '=', self.lot_name),
                        ])
                        if counter > 0:
                            message = _(
                                'Existing Serial number (%s). Please correct the serial number encoded.') % self.lot_name
                elif self.lot_id:
                    self.lot_expired_date = self.lot_id.use_date
                    counter = Counter(move_lines_to_check.mapped('lot_id.id'))
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _(
                            'You cannot use the same serial number twice. Please correct the serial numbers encoded.')

            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    def _compute_show_lot_user_date(self):
            _logger.info("_compute_show_lot_user_date")
            for ml in self:
                ml.lot_use_date = ml.lot_id.use_date
                if ml.lot_id:
                    ml.lot_id_po = ml.lot_id
                else:
                    ml.lot_id_po = None


    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_tracked_without_lot = OrderedSet()
        ml_ids_to_delete = OrderedSet()
        ml_ids_to_create_lot = OrderedSet()
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                   defined on the unit of measure "%s". Please change the quantity done or the \
                                   rounding precision of your unit of measure.') % (
                ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name:
                                if ml.product_id.tracking == 'lot' and not ml.lot_id:
                                    # customize code start
                                    params = self.env['ir.config_parameter'].sudo()
                                    production_lot_alert_days = int(
                                        params.get_param('inventory_extension.production_lot_alert_days'))
                                    if ml.lot_expired_date and ml.lot_expired_date is not None:
                                        final_date = fields.Datetime.from_string(ml.lot_expired_date)
                                        if production_lot_alert_days > 0:
                                            alert_date = final_date.date() - datetime.timedelta(
                                                days=production_lot_alert_days)
                                        else:
                                            alert_date = final_date.date() - datetime.timedelta(days=3)
                                        lot = self.env['stock.lot'].create(
                                            {'name': ml.lot_name, 'use_date': ml.lot_expired_date,
                                             'removal_date': ml.lot_expired_date,
                                             'expiration_date': ml.lot_expired_date,
                                             'alert_date': str(alert_date), 'product_id': ml.product_id.id})
                                    # customize code end
                                    else:
                                        lot = self.env['stock.lot'].search([
                                            ('company_id', '=', ml.company_id.id),
                                            ('product_id', '=', ml.product_id.id),
                                            ('name', '=', ml.lot_name),
                                        ], limit=1)
                                    if lot:
                                        ml.lot_id = lot.id
                                    else:
                                        ml_ids_to_create_lot.add(ml.id)
                                else:
                                    ml_ids_to_create_lot.add(ml.id)
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.is_inventory:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id and ml.id not in ml_ids_to_create_lot:
                        ml_ids_tracked_without_lot.add(ml.id)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_ids_to_delete.add(ml.id)

        if ml_ids_tracked_without_lot:
            mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
            raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
                            '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))
        ml_to_create_lot = self.env['stock.move.line'].browse(ml_ids_to_create_lot)
        ml_to_create_lot._create_and_assign_production_lot()

        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()

        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()

        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        for ml in mls_todo:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding
                # TODO: UPD ODOO16 NOTE Code Commented out for now.
                # if this move line is force assigned, unreserve elsewhere if needed
                # if not ml._should_bypass_reservation() and float_compare(ml.qty_done, ml.product_uom_qty,
                #                                                                        precision_rounding=rounding) > 0:
                #     qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id,
                #                                                                rounding_method='HALF-UP')
                #     extra_qty = qty_done_product_uom - ml.product_qty
                #     ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
                #     ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id,
                #                          package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
                # unreserve what's been reserved
                # if not ml._should_bypass_reservation(
                #         ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                #     try:
                #         Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty,
                #                                         lot_id=ml.lot_id,
                #                                         package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                #     except UserError:
                #         Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False,
                #                                         package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                               rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                          lot_id=ml.lot_id, package_id=ml.package_id,
                                                                          owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                  package_id=ml.package_id, owner_id=ml.owner_id,
                                                                  strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                         lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                         lot_id=ml.lot_id, package_id=ml.package_id,
                                                         owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                 package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            ml_ids_to_ignore.add(ml.id)
        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.with_context(bypass_reservation_update=True).write({
            'reserved_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })


class ProductionLotNameAppendDate(models.Model):
    _inherit = 'stock.lot'


    def name_get(self):
        result = []
        if self.env.context is None:
            self.env.context = {}
        for record in self:
            name = record.name
            if self.env.context.get('lot_date_display_name_so'):

                pick_id = self.env.context.get('active_picking_id')
                pick_obj = request.env['stock.picking'].search([('id', '=', pick_id)])
                stock_move = request.env['stock.move'].search([('picking_id', '=', pick_id)])
                aval_qty = request.env['stock.quant']._get_available_quantity\
                    (record.product_id,stock_move.location_id,lot_id=record,package_id=None,
                     owner_id=None, strict=False,allow_negative=False)

                if record.use_date:
                    name = record.name + ': #Exp Date :' + str(record.use_date)[0:10]\
                           + ':#Qty :' +str(record.product_qty) + ':#Avl Qty :' +str(aval_qty)
                else:
                    name = record.name

                result.append((record.id, name))

            elif self.env.context.get('lot_date_display_name_po'):
                if record.use_date:
                    name = record.name + ': #Exp Date :' + str(record.use_date)[0:10] + ':#Qty :' + str(record.product_qty)
                else:
                    name = record.name
                result.append((record.id, name))

            else:
                result.append((record.id, name))

        return result
