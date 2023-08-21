odoo.define('account_pass.pass_jquery', function (require) {
    'use strict';

    var rpc = require('web.rpc');

    $(window).on('hashchange', function() {
        console.log('Hey .............. 1')
      $('.abc').closest('td').closest('tr').find('td:first').find('label:first').css("text-decoration", "underline");
       });
});
