odoo.define('account_pass.pass_jquery', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    $(window).on('hashchange', function() {
        var url_loader = window.location.href;
        if (url_loader.includes('model=account.pass&view_type=form')) {
            $('.label_underline').closest('td').closest('tr').find('td:first').find('label:first').css("border-bottom", "2px solid");
        }
       });
});
