from odoo import api, models


class ReportPickTicketOrderOrDate(models.AbstractModel):
    _name = 'report.pick_ticket.pick_ticket_report1'

    @api.model
    def get_report_values(self, docids, data=None):
        pick_report = self.env['report.order.pick.ticket'].search([('id','in',docids)], order='sale_id')

        old = 0
        picks = {}
        for pick in pick_report:
            product = {'quantity': int(float(pick.qty_done)),
                                 'product': pick.product_id.name,
                                 'location': pick.location_id.display_name,
                                 'destination': pick.location_dest_id.display_name}
            if old == pick.sale_id.id:
                picks[old]['product'].append(product)
            else:
                old = pick.sale_id.id
                picks[old] = {
                    'order': pick.sale_id.name,
                    'customer': pick.partner_id.display_name,
                    'carrier': pick.carrier_info,
                    'state': pick.state,
                    'product': [product]}

        return {'picks': picks}
