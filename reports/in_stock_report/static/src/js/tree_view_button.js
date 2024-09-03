/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
//import { session } from "@web/session";
import { blockUI, unblockUI } from "web.framework";
var session = require('web.session');

export class InStockReportListController extends ListController {
    setup() {
        super.setup();
//        this.archiveEmployee = useArchiveEmployee();
    }
    async onClickExport() {
        this.filter_button()
    }
    filter_button() {
        console.log("------------343aa-----------")
        blockUI();
        this.getSession().get_file({
            url: '/web/export/in_stock_report',
            complete: unblockUI,
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            success: function(){
                console.log("------------aa-----------")
                unblockUI()
            }
        })

    }
}

registry.category('views').add('in_stock_list', {
    ...listView,
    Controller: InStockReportListController,
    buttonTemplate: 'in_stock_report.buttons',
});

