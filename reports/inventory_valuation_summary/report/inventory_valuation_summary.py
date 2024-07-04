from odoo import api, models


class ReportInventoryProductValuationSummary(models.AbstractModel):
    _name = 'report.inventory_valuation_summary.inventory_valuation_template'
    _description = 'Report Inventory Product Valuation Summary'

    @api.model
    def _get_report_values(self, docids, data=None):

        print("--------------Start--------------------")
        data = []
        warehouses = self.env['report.inventory.valuation.summary'].read_group(domain=[], fields=[],
                                                                               groupby=['warehouse', 'location',
                                                                                        'type'])
        for warehouse_rec in warehouses:
            warehouse = {
                'warehouse': warehouse_rec['warehouse'],
                'warehouse_count': warehouse_rec['warehouse_count'],
                'quantity': warehouse_rec['quantity'],
                'locations': [],
                'hasRecord': False
            }
            data.append(warehouse)

            locations = self.env['report.inventory.valuation.summary'].read_group(domain=warehouse_rec['__domain'],
                                                                                  fields=[],
                                                                                  groupby=warehouse_rec['__context'][
                                                                                      'group_by'])
            warehouse_rec['locations'] = locations
            for location_rec in locations:
                location = {
                    'location': location_rec['location'],
                    'location_count': location_rec['location_count'],
                    'quantity': location_rec['quantity'],
                    'types': [],
                    'hasRecord': False
                }
                warehouse['locations'].append(location)

                types = self.env['report.inventory.valuation.summary'].read_group(domain=location_rec['__domain'],
                                                                                  fields=[],
                                                                                  groupby=location_rec['__context'][
                                                                                      'group_by'])
                location_rec['types'] = types
                for type_rec in types:
                    type_rec['__domain'].append(('id', 'in', docids))
                    type = {
                        'type': type_rec['type'],
                        'type_count': type_rec['type_count'],
                        'quantity': type_rec['quantity'],
                        'record': self.env['report.inventory.valuation.summary'].search_read(
                            domain=type_rec['__domain'])
                    }

                    if location['hasRecord'] == False and len(type['record']) > 0:
                        location['hasRecord'] = True

                    if warehouse['hasRecord'] == False and len(type['record']) > 0:
                        warehouse['hasRecord'] = True

                    location['types'].append(type)
        print("--------------end--------------------")
        return {
            'warehouses': data
        }