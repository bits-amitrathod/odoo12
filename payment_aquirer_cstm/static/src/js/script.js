odoo.define('payment_aquirer_cstm.payment_aquirer_cstm', function(require) {
    "use strict";
    require('web.dom_ready');
    var ajax = require('web.ajax');

    $(document).ready(function() {
        ajax.jsonRpc("/checkHavingCarrierWithAccountNo", 'call', {
            }).then(function(data) {
                var carrier_acc_no = data['carrier_acc_no']
                if (carrier_acc_no) {
                    $("#delivery_35").prop('checked', true);
                    $("#hasShippingNote").prop('checked', true);
                } else {
                    $("#hasShippingNote").prop('checked', false);
                    $("#delivery_35").prop('checked', false);
                    $("#delivery_3").prop('checked', true);
                    $("#hasShippingNote").parent().hide();
                    $("#expedited_shipping").hide();
                    $("#editShippingNote").hide();
                    $("#delivery_35").parent().hide();
                }
         });

          var default_e = document.getElementById("selectDeliveryMethod");
          var default_value = default_e.options[default_e.selectedIndex].value;
          document.getElementById("noteText").value = default_value;

        $("#hasShippingNote").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping").show();
                $("#editShippingNote").show();
                $("#delivery_35").prop('checked', true);
            } else {
                $("#expedited_shipping").hide();
                $("#editShippingNote").hide();
                $("#delivery_35").prop('checked', false);
            }
        });

        $("#delivery_35").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', true);
                $("#editShippingNote").show();
                $("#expedited_shipping").show();


            }
        });

        $("#delivery_3").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_4").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_5").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_6").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_7").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_8").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#delivery_16").change(function() {
            if ( $(this).is(':checked') ) {
                $("#hasShippingNote").prop('checked', false);
                $("#editShippingNote").hide();
                $("#expedited_shipping").hide();
            }
        });

        $("#selectDeliveryMethod").change(function() {
            var e = document.getElementById("selectDeliveryMethod");
            var value = e.options[e.selectedIndex].value;
            if(value === "other"){
                document.getElementById("noteText").value = "";
                document.getElementById("noteText").removeAttribute('readonly');
                document.getElementById("noteText").setAttribute('required', true);
            } else {
                document.getElementById("noteText").value = value;
                document.getElementById("noteText").setAttribute('readonly', true);
            }
        });
    });
});