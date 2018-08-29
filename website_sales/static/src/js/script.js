odoo.define('website_sales.website_sales', function (require) {
    "use strict";
    require('web.dom_ready');
    var ajax = require('web.ajax');

     var clickwatch = (function(){
              var timer = 0;
              return function(callback, ms){
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
              };
    })();


    $('input[name="customerReferenceSO"]').on("change", function (event) {
    var self = $(this);
        clickwatch(function(){
            ajax.jsonRpc("/shop/cart/updatePurchaseOrderNumber", 'call', {
                'purchase_order': self.val()
            }).then(function (data) {
//            console.log("data------------>",data);
            });
          }, 500);
      });
});