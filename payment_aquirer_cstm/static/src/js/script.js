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
//----------------- Checkbox Shipping -------------------------------   delivery_carrier
        $('#hasShippingNote').on("change", function (event) {
            if(event.target.checked){
                $(delivery_carrier).hide();
                $("#"+freeShipingLabel.value).prop('checked', true).click();
                $("#editShippingNote").show();
                 if($("#noteText").val() ==""){
                    $('#accept').modal('show');
                }

            }else{
                $("#editShippingNote").hide();
                $(delivery_carrier).show()
                 var self = $(this);
                clickwatch(function(){

                    ajax.post("/shop/cart/expeditedShipping",{expedited_shipping:""}).then(function (data) {
                        window.hasShippingNoteValue == null;
                        $("#noteText").val("");
                        $("#expedited_shipping").hide()
                    });
                }, 500);
            }
        });

        if(expedited_shipping.innerText == ""){
            $("#expedited_shipping").hide()
        }

        $('#accept').on('hidden.bs.modal', function () {
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