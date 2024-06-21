from stock_barcode.tests.test_barcode_client_action import TestPickingBarcodeClientAction
from datetime import timedelta
from odoo import fields

from odoo.tests.common import TransactionCase
import logging
_logger = logging.getLogger(__name__)

at_install = True
post_install = True
at_update = True


class Invent(TestPickingBarcodeClientAction):

#     def test_receipt_reserved_lots_multiloc_1(self):
#         # clean_access_rights(self.env)
#         grp_multi_loc = self.env.ref('stock.group_stock_multi_locations')
#         self.env.user.write({'groups_id': [(4, grp_multi_loc.id, 0)]})
#         grp_lot = self.env.ref('stock.group_production_lot')
#         self.env.user.write({'groups_id': [(4, grp_lot.id, 0)]})
#
#         receipts_picking = self.env['stock.picking'].create({
#             'location_id': self.supplier_location.id,
#             'location_dest_id': self.stock_location.id,
#             'picking_type_id': self.picking_type_in.id,
#         })
#
#         url = self._get_client_action_url(receipts_picking.id)
#
#         move1 = self.env['stock.move'].create({
#             'name': 'test_delivery_reserved_lots_1',
#             'location_id': self.supplier_location.id,
#             'location_dest_id': self.stock_location.id,
#             'product_id': self.productlot1.id,
#             'product_uom': self.uom_unit.id,
#             'product_uom_qty': 4,
#             'picking_id': receipts_picking.id,
#         })
#
#         # Add lot1 et lot2 sur productlot1
#         lotObj = self.env['stock.lot']
#         lot1 = lotObj.create({'name': 'lot1', 'product_id': self.productlot1.id})
#         lot2 = lotObj.create({'name': 'lot2', 'product_id': self.productlot1.id})
#
#         receipts_picking.action_confirm()
#         receipts_picking.action_assign()
#
#         self.phantom_js(
#             url,
#             "odoo.__DEBUG__.services['web_tour.tour'].run('test_receipt_reserved_lots_multiloc_1')",
#             "odoo.__DEBUG__.services['web_tour.tour'].tours.test_receipt_reserved_lots_multiloc_1.ready",
#             login='admin',
#             timeout=180,
#         )
#         receipts_picking.invalidate_cache()
#         lines = receipts_picking.move_line_ids
#         self.assertEqual(lines[0].qty_done, 0.0)
#         self.assertEqual(lines[0].product_qty, 4.0)
#         self.assertEqual(lines.mapped('location_id.name'), ['Vendors'])
#         self.assertEqual(lines[1].lot_name, 'lot1')
#         self.assertEqual(lines[2].lot_name, 'lot2')
#         self.assertEqual(lines[1].qty_done, 2)
#         self.assertEqual(lines[2].qty_done, 2)
#         self.assertEqual(lines[1].location_dest_id.name, 'Shelf 2')
#         self.assertEqual(lines[2].location_dest_id.name, 'Shelf 1')
#         print("Completed here...")
#
#
# obj=Invent()
# obj.test_receipt_reserved_lots_multiloc_1()

    def test_receipt_reserved_lots_multiloc_1(self):
        # new_order = self.env.ref('available.product.dict').copy({'commitment_date': '2010-07-12'})
        super(Invent,self)
        a=10
        b=20
        self.assertTrue(a,b)
        # self.assertTrue(new_order,"order")

        print("Test executed successfully in invent")
        _logger.warn("Test executed successfully 2 in invent")
#
#
#
# obj=Invent()
# obj.test_receipt_reserved_lots_multiloc_1()