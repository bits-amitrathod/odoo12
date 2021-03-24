odoo.define('payment_aquirer_cstm.payment_aquirer_cstm', function(require) {
    "use strict";
    require('web.dom_ready');
    var ajax = require('web.ajax');
    var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .badge:not(.o_delivery_compute)');
    var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=3] ~ .o_delivery_compute');
    var salesTeamMessage = $('textarea[name="sales_team_message"]');

    $(document).ready(function() {
        ajax.jsonRpc("/checkHavingCarrierWithAccountNo", 'call', {
            }).then(function(data) {
                var carrier_acc_no = data['carrier_acc_no']
                console.log(carrier_acc_no);
                if (carrier_acc_no) {
                    $("#my_shipper_account_radio").prop('checked', true);
                    $("#delivery_35").prop('checked', true);
                    $("#expedited_shipping_div").parent().show();
                    $("#choose_a_delivery_method_label").parent().hide();
                    $("#delivery_method_custom").parent().hide();
                } else {
                    $("#shipping_options").hide();
                    $("#delivery_35").prop('checked', false);
                    $("#delivery_3").prop('checked', true);
                    $("#expedited_shipping_div").parent().hide();
                    $("#delivery_35").parent().hide();
                    console.log('Error message');
                    console.log(data['error_message']);
                    console.log(data['amount_delivery']);
                    console.log(data['status']);
                    if (data['status'] === true){
                        console.log('in if blog');
                        $carrier_badge.children('span').text(data['amount_delivery']);
                        $carrier_badge.removeClass('d-none');
                        $compute_badge.addClass('d-none');
                    }else{
                        console.log('in else blog');
                        $carrier_badge.addClass('d-none');
                        $compute_badge.removeClass('d-none');
                        $compute_badge.text(data['error_message']);
                    }
                }
         });


        $("#delivery_35").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().show();
                var e = document.getElementById("selectDeliveryMethod");
                var value = e.options[e.selectedIndex].value;
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': value
                });
            }
        });

        $("#delivery_3").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_4").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_5").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_6").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_7").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_8").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#delivery_16").change(function() {
            if ( $(this).is(':checked') ) {
                $("#expedited_shipping_div").parent().hide();
                ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                    'expedited_shipping': ""
                });
            }
        });

        $("#selectDeliveryMethod").change(function() {
            var e = document.getElementById("selectDeliveryMethod");
            var value = e.options[e.selectedIndex].value;
            console.log(value);
            ajax.jsonRpc("/shop/cart/expeditedShipping", 'call', {
                'expedited_shipping': value
            });
        });
    });


    salesTeamMessage.on("change", function(event) {
        ajax.jsonRpc("/salesTeamMessage", 'call', {
            'sales_team_message': salesTeamMessage.val()
        });
    });
});