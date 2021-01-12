odoo.define('website_sales.quote_my_report_cart', function (require) {
'use strict';

    require('web.dom_ready');
    var base = require("web_editor.base");
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    require("website.content.zoomodoo");
    var _t = core._t;


	$('.engine').each(function () {
	    var engine = this;
        $(engine).on('click', 'a.delete_product', function (ev) {
            console.log('In client_order_ref');
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var product_id = $input[0]['attributes']['data-product-id']['value'];
            var partner_id = $input[0]['attributes']['data-partner-id']['value'];
            console.log(product_id)
            var r = confirm("Are You Sure, You want to remove product?");
              if (r == true) {
                     ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                        'product_id': product_id,
                        'partner_id': partner_id,
                        'set_qty': 0,
                    }).then(function (data) {
//                        window.location.reload();
                        console.log('return');
                        console.log(data);
                    });
              } else {
                    console.log("inside false block")
                    return false;
              }
        });


//        $(engine).on('click', 'a.add_cart_json', function (ev) {
//            console.log('In add quantity');
//
//        });
   });
});
