from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo import api, models


class ReportPickTicketOrderOrDate(models.AbstractModel):
    _name = 'report.pick_ticket.pick_ticket_report1'
    _description = 'ReportPickTicketOrderOrDate'

    @api.model
    def _get_report_values(self, docids, data=None):
        pick_report = self.env['report.pick.ticket'].search([('id', 'in', docids)], order='picking_id')

        old = 0
        picks = {}
        for pick in pick_report:
            product = {'quantity': int(float(pick.qty_done)),
                       'product': pick.product_id.name,
                       'location': pick.location_id.display_name,
                       'destination': pick.location_dest_id.display_name,
                       'product_uom': pick.product_uom_id.name}
            if old == pick.picking_id.id:
                picks[old]['product'].append(product)
            else:
                old = pick.picking_id.id
                picks[old] = {
                    'order': pick.sale_id.name,
                    'customer': pick.partner_id.display_name,
                    'carrier': pick.carrier_info,
                    'state': pick.state,
                    'priority': PROCUREMENT_PRIORITIES[int(pick.priority)][1],
                    'scheduled_date': pick.scheduled_date,
                    'picking_type': pick.picking_type_id.name,
                    'warehouse': pick.warehouse_id.name,
                    'picking': pick.picking_id.name,
                    'product_uom': pick.product_uom_id.name,
                    'product': [product]}

        popup = self.env['popup.pick.ticket'].search([('create_uid', '=', self._uid)], limit=1,
                                                     order="id desc")

        return {'picks': picks, 'popup': popup}