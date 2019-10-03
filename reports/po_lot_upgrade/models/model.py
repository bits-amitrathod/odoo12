from odoo import api, fields, models, tools
import odoo.addons.decimal_precision as dp

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

class PickTicketReport(models.TransientModel):
    _name = "po.lot"

    def upgrade(self):
        print("Upgread Lot")
        xl_workbook = xlrd.open_workbook("D:/tushar/sps_project/sps/reports/po_lot_upgrade/poLotsheet.xlsx")
        sheet = xl_workbook.sheet_by_name(xl_workbook.sheet_names()[0])
        for i in range(sheet.nrows):
            SQL = 'update stock_picking  set note=\''+ sheet.cell_value(i, 1) + '\'  WHERE origin = \''+ sheet.cell_value(i, 0).strip()+ '\''
            print(SQL)
            self._cr.execute(SQL)