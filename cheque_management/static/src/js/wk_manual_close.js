odoo.define('odoo_cheque_management.wk_manual_close', function (require) {
    'use strict';
    console.log("-------Backend------------------");
    // $(document).find('.wk_manual_close').on('click', function (e) { 
    $(document).on('click', '.wk_manual_close', function (event){
        console.log("-------------wk_manual_close---------------");
        $('.wk_cancel_btn').click();
    });
});