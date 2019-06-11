from odoo import api, models


class ReportSpsReceivingList(models.AbstractModel):
    _name = 'report.sps_receiving_list_report.adjustment_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        stock_move_lines = self.env['stock.move.line'].search([('id', 'in', docids)], order='product_id')
        old = 0
        receiving_list = {}
        for move_lines in stock_move_lines:
            lot = {
                'lot_id': move_lines.lot_id.name,
                'lot_expired_date': move_lines.lot_expired_date,
                'qty_done': int(float(move_lines.qty_rece)),
                'product_uom_id': move_lines.product_uom_id.name,
            }
            if old == move_lines.product_id.id:
                receiving_list[old]['lots'].append(lot)
            else:
                product_name = ""
                if not move_lines.sku_code is False:
                    product_name = move_lines.sku_code + " - "

                old = move_lines.product_id.id
                receiving_list[old] = {
                    'product': product_name + move_lines.product_id.name,
                    'purchase_order_id': move_lines.purchase_order_id,
                    'purchase_partner_id': move_lines.purchase_partner_id,
                    'lots': [lot]}

        return {'receiving_list': receiving_list}