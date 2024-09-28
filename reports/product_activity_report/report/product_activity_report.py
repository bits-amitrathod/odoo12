from odoo import api, models


class ReportProductActivityReport(models.AbstractModel):
    _name = 'report.product_activity_report.product_activity_report_template'
    _description = 'Report Product Activity Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        self.env.cr.execute(""" SELECT * FROM product_activity_report where id in (""" + ",".join(map(str, docids)) + """)
        order by location,type """)
        warehouses = self.env.cr.dictfetchall()

        popup = self.env['product.activity.report.popup'].search([('create_uid', '=', self._uid)], limit=1,
                                                                 order="id desc")


        oldType = ""
        oldLocation = ""
        activities = {}
        for activity in warehouses:
            product = {'event': activity['event'],
                       'date': activity['date'],
                       'change_qty': activity['change_qty'],
                       'agent': activity['agent'],
                       'sku': activity['sku'],
                       'lot': activity['lot'],
                       'expiration_date': activity['expiration_date'],
                       }
            if oldLocation == activity['location']:
                if oldType == activity['type']:
                    activities[oldLocation][oldType].append(product)
                else:
                    oldType = activity['type']
                    activities[oldLocation][oldType] = [product]
            else:
                oldLocation = activity['location']
                oldType = activity['type']
                activities[oldLocation] = {oldType: [product]}
        return {
            'activities': activities,'popup':popup

        }
