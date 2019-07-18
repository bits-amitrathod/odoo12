odoo.define('payment_aquirer_cstm.payment_aquirer_cstm', function (require) {
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

                });
            }, 500);
        });






        $('#hasShippingNote').on("change", function (event) {
            if(event.target.checked){
                $("#editShippingNote").show();
                 if($("#noteText").val() ==""){
                    $('#accept').modal('show');
                }

            }else{
                $("#editShippingNote").hide();
                 var self = $(this);
                clickwatch(function(){

                    ajax.post("/shop/cart/expeditedShipping",{expedited_shipping:""}).then(function (data) {
                        window.hasShippingNoteValue == null;
                        $("#noteText").val("");
//                        console.log("----ajax-------",data);
                    });
                }, 500);
            }
        });

        $('#accept').on('hidden.bs.modal', function () {
        console.log("-----------");
            $("#noteText").val(window.hasShippingNoteValue);
            if(window.hasShippingNoteValue == null){
               $('#hasShippingNote').prop('checked', false).trigger("change");
            }
        });


        if($("#noteText").val()!= ""){
            window.hasShippingNoteValue = $("#noteText").val();
            $('#hasShippingNote').prop('checked', true).trigger("change");
        }else{
            window.hasShippingNoteValue = null;
            $('#hasShippingNote').prop('checked', false).trigger("change");
        }
});