from odoo import api, models,_
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')


class MtdReportModel(models.AbstractModel):
    _name = 'report.mtd_sales.mtd_temp'
    _description = "Mtd Report Model"

    def get_report_values(self, docids, data=None):

        action = self.env.ref('mtd_sales.action_report_mtd_sales').report_action([], data={})
        action.update({'target': 'main'})

        # return {
        #     'type': 'ir.actions.act_window',
        #     'views': [(self.env.ref('mtd_sales.mtd_sales_graph_view').id, 'graph')],
        #     'view_mode': 'graph',
        #     'name': _('MTD Sales'),
        #     'res_model': 'mtd_sales',
        #     'domain': [('id', 'in', (docids))],
        #     'target': 'main',
        # }

        return action

    def _get_objs_for_report(self, docids, data):
        if docids:
            ids = docids
        elif data and 'context' in data:
            ids = data["context"].get('active_ids', [])
        else:
            ids = self.env.context.get('active_ids', [])
        return self.env[self.env.context.get('active_model')].browse(ids)

    def create_xlsx_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, self.get_workbook_options())
        self.generate_xlsx_report(workbook, data, objs)


        workbook.close()
        file_data.seek(0)
        return file_data.read(), 'xlsx'

    def get_workbook_options(self):
        return {}

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            sheet = workbook.add_worksheet('Report')
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.name, bold)

