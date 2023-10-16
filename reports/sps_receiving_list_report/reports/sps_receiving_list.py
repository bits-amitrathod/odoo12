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
                'exp_date': move_lines.exp_date,
                'qty_done': int(float(move_lines.qty_rece)),
                'date_done': move_lines.picking_id.date_done,
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
                    'lots': [lot],
                    'prod_id': old
                }


        new_receiving_list = {}
        count = 0
        for obj in receiving_list:
            dict_new = receiving_list[obj]
            prod_id = dict_new['prod_id']
            pur_id = dict_new['purchase_order_id']
            ven_id = dict_new['purchase_partner_id']
            if len(new_receiving_list) > 0:
                flag_ck = False
                for obj_list in new_receiving_list.copy():
                    dict_new_list = new_receiving_list[obj_list]
                    dist_list = dict_new_list['data']
                    if dict_new_list['po_order_no'] == dict_new['purchase_order_id']:
                        # for_update_list = new_receiving_list[obj_list]['data']
                        dist_list.update({prod_id: dict_new})
                        flag_ck = True
                        # new_receiving_list[obj_list]['data'] = for_update_list
                if flag_ck == False:
                    short = None
                    extra = None
                    purchase_order = self.env['purchase.order'].search([('name', '=', pur_id)], limit=1)
                    for po in purchase_order:
                        for pick in po.picking_ids:
                            if pick.picking_type_id.id == 2:
                                short = pick.short
                                extra = pick.extra
                new_receiving_list[count] = {
                        'po_order_no': pur_id,
                        'data': {prod_id: dict_new},
                        'ven_id': ven_id,
                        'short': short,
                        'extra': extra
                    }

            else:
                short = None
                extra = None
                purchase_order = self.env['purchase.order'].search([('name', '=', pur_id)], limit=1)
                for po in purchase_order:
                    for pick in po.picking_ids:
                        if pick.picking_type_id.id == 2:
                            short = pick.short
                            extra = pick.extra
                new_receiving_list[count] = {
                    'po_order_no': pur_id,
                    'data': {prod_id: dict_new},
                    'ven_id': ven_id,
                    'short': short,
                    'extra': extra
                }
            count = count + 1

        return {'new_receiving_list': new_receiving_list}

class ReportSpsReceivingList1(models.AbstractModel):
    _name = 'report.sps_receiving_list_report.adjustment_report1'

    @api.model
    def _get_report_values(self, docids, data=None):
        stock_move_lines = self.env['stock.move.line'].search([('picking_id', 'in', docids)], order='product_id')
        old = 0
        receiving_list = {}
        for move_lines in stock_move_lines:
            lot = {
                'lot_id': move_lines.lot_id.name,
                'exp_date': move_lines.exp_date,
                'qty_done': int(float(move_lines.qty_rece)),
                'date_done': move_lines.picking_id.date_done,
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
                    'lots': [lot],
                    'prod_id': old
                }

        new_receiving_list = {}
        count = 0
        for obj in receiving_list:
            dict_new = receiving_list[obj]
            prod_id = dict_new['prod_id']
            pur_id = dict_new['purchase_order_id']
            ven_id = dict_new['purchase_partner_id']
            if len(new_receiving_list) > 0:
                flag_ck = False
                for obj_list in new_receiving_list.copy():
                    dict_new_list = new_receiving_list[obj_list]
                    dist_list = dict_new_list['data']
                    if dict_new_list['po_order_no'] == dict_new['purchase_order_id']:
                        # for_update_list = new_receiving_list[obj_list]['data']
                        dist_list.update({prod_id: dict_new})
                        flag_ck = True
                        # new_receiving_list[obj_list]['data'] = for_update_list
                if flag_ck == False:
                    short = None
                    extra = None
                    purchase_order = self.env['purchase.order'].search([('name', '=', pur_id)], limit=1)
                    for po in purchase_order:
                        for pick in po.picking_ids:
                            if pick.picking_type_id.id == 2:
                                short = pick.short
                                extra = pick.extra
                    new_receiving_list[count] = {
                        'po_order_no': pur_id,
                        'data': {prod_id: dict_new},
                        'ven_id': ven_id,
                        'short': short,
                        'extra': extra

                    }

            else:
                short = None
                extra = None
                # purchase_order = self.env['purchase.order'].search([('name', '=', pur_id)], limit=1)
                # for po in purchase_order:
                #     for pick in po.picking_ids:
                #         if pick.picking_type_id.id == 2:
                #             short = pick.short
                #             extra = pick.extra
                stock_picking = self.env['stock.picking'].search([('id', 'in', docids)])
                for stock_obj in stock_picking:
                    short = stock_obj.short
                    extra = stock_obj.extra

                new_receiving_list[count] = {
                    'po_order_no': pur_id,
                    'data': {prod_id: dict_new},
                    'ven_id': ven_id,
                    'short': short,
                    'extra': extra
                }
            count = count + 1

        return {'new_receiving_list': new_receiving_list}
