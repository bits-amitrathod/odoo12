odoo.define('website_sales.quote_my_report_cart', function (require) {
'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var session = require('web.session');
    var rpc = require('web.rpc')
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    //var framework = require('web.framework');
//    require("web.zoomodoo");
    var _t = core._t;

    $(document).ready(function() {
                var url_loader = window.location.href
                if(url_loader.includes('shop/quote_my_report') || url_loader.includes('shop/cart?flag') || url_loader.includes('shop/cart')){
                    $('#loader_in_stock').show();
                }
                function disableBack() {

                var url_temp = window.location.href
                if(url_temp.includes('shop/cart?flag') || url_temp.includes('shop/cart')){
                    history.pushState(null, null, window.location.href);
                    history.back();
                    window.onpopstate = () => history.forward();
                     $('#loader_in_stock').hide();
                }
                }
                window.onload = disableBack();
                window.onpageshow = function(e) {
                    if (e.persisted)
                        disableBack();
                }
                setTimeout(function (){
                    $('#loader_in_stock').hide();
                }, 2000);

            });

    $('#add_product_in_to_cart').click(function (ev) {

        console.log('in add cart js fun start');
         $("#add_product_in_to_cart").attr('disabled', true);
           $('#loader_in_stock').show();
        var $form = $('#quote_products').closest('form');
        $form.submit();
        ev.preventDefault();
        let prod_list =[];
        let new_qty_list =[];
        var partner_id;
        var input_box_list = $('#quote_products').closest('table').find('td input:text');
        $(input_box_list).each(function () {
            var $input = $(this).parent().parent().parent().find("td input:checkbox");
            console.log($input);
            if ($input[0].checked==true){
              var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
              partner_id = parseInt($input[0]['attributes']['data-partner-id']['value']);
              prod_list.push(parseInt(product_id));
              new_qty_list.push(parseInt(this.value));
            }
          });

           ajax.jsonRpc("/shop/quote_my_report/update_json_list", 'call', {
                        'partner_id': partner_id,
                        'product_id': prod_list,
                         'new_qty': new_qty_list,

                    }).then(function (data) {
                        console.log('return');
                        //console.log(data);
                       //$form.submit();
                        ajax.post("/add/product/cart", {
                        }).then(function (data) {
                            console.log('return add to cart');
                             $("#add_product_in_to_cart").attr('disabled', false);
                              console.log('in add cart js call end');
                                $('#loader_in_stock').hide();
                            window.location.href = window.location.origin + '/shop/cart?flag=True&partner='+partner_id
                        });
            });

        console.log('in add cart js fun end');
    });

    $('#selectAll').click(function (ev) {
        console.log('checked all');
        $(this).closest('table').find('td input:checkbox').prop('checked', this.checked);
        var $link = $(ev.currentTarget);
        var $input = $link.parent().find("input");
        var val = $input.prop('checked');

        if (val === true){
            $('[id^=row_checked_]').addClass('row-checked')
            $('[id^=allow_qty_plus_]').css({'pointer-events':'', 'color':'#3d9cca'});
            $('[id^=allow_qty_minus_]').css({'pointer-events':'', 'color':'#3d9cca'});
            $('[id^=input_qty_]').css({'pointer-events':'', 'color':'#3d9cca'});
        } else {
            $('[id^=row_checked_]').removeClass('row-checked')
            $('[id^=allow_qty_plus_]').css({'pointer-events':'none', 'color':'#cacaca'});
            $('[id^=allow_qty_minus_]').css({'pointer-events':'none', 'color':'#cacaca'});
            $('[id^=input_qty_]').css({'pointer-events':'none', 'color':'#cacaca'});
        }

       /* ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                        'select': val
                    }).then(function (data) {
                        console.log('return');
                        console.log(data);
            });*/
    });

	$('.report').each(function () {
	    var engine = this;

        $(engine).on('click', 'a.js_add_cart_json', function (ev) {
            console.log('In add quantity');
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().parent().find("input");
            var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
            var available_qty = parseInt($input[0]['attributes']['data-available-qty']['value']);
            var partn_name_id = $input[0]['attributes']['data-partn-name-id']['value'];
            var partner_id = parseInt($input[0]['attributes']['data-partner-id']['value']);
            var new_qty = parseInt($input.val());
            console.log(partn_name_id);
            var ele1 = $link.parent().find("#allow_qty_plus_"+partn_name_id);
            if (new_qty>=available_qty) {
               $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
            }else{
               $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});
            }

           /* ajax.jsonRpc("/shop/quote_my_report/update_json", 'call', {
                        'partner_id': partner_id,
                        'product_id': product_id,
                        'new_qty': new_qty,
                    }).then(function (data) {
                        console.log('return');
                        console.log(data);
            });*/
        });

        $(engine).on('change', 'input.input_qty_1', function (ev) {
            console.log('input button');
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().parent().find("input");
            var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
            var available_qty = parseInt($input[0]['attributes']['data-available-qty']['value']);
            var partn_name_id = $input[0]['attributes']['data-partn-name-id']['value'];
            var partner_id = parseInt($input[0]['attributes']['data-partner-id']['value']);
            var new_qty = parseInt($input.val());
            console.log(partn_name_id);
            var ele1 = $link.parent().find("#allow_qty_plus_"+partn_name_id);
            if (new_qty>=available_qty) {
               $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
               console.log('new Entered Qty is greater than available qty');
//               alert("New Entered Qty is greater than available qty")
               $('#input_qty_'+partn_name_id).val(available_qty)
               Dialog.alert(this, "New Entered Qty is greater than available qty");

            }else{
               $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});
            }
        });

        $(engine).on('click', 'input:checkbox', function (ev) {
            console.log('checked one');
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            if ('data-partn-name-id' in $input[0]['attributes']) {
                var partn_name_id = parseInt($input[0]['attributes']['data-partn-name-id']['value']);
                console.log(parseInt($input[0]['attributes']['data-partner-id']['value']));
                var partner_id = parseInt($input[0]['attributes']['data-partner-id']['value']);
                var available_qty = parseInt($input[0]['attributes']['data-available-qty']['value']);
                var new_qty = parseInt($('#input_qty_'+partn_name_id).val());
                var val = $input.prop('checked');
                console.log(partner_id);
                if(val === true){
                    $('#row_checked_'+partn_name_id).addClass('row-checked')
                    if (new_qty >= available_qty) {
                        $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                    }
                    else{
                    $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});
                    $('#input_qty_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});

                    }
                    $('#allow_qty_minus_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});
                    $('#input_qty_'+partn_name_id).css({'pointer-events':'', 'color':'#3d9cca'});

                }else{
                    $('#row_checked_'+partn_name_id).removeClass('row-checked')
                    $('#allow_qty_plus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                    $('#allow_qty_minus_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                    $('#input_qty_'+partn_name_id).css({'pointer-events':'none', 'color':'#cacaca'});
                }
            }

            if ($('td input:checked').length > 0) {
                $("#add_product_in_to_cart").attr('disabled', false);
            } else {
                $("#add_product_in_to_cart").attr('disabled', true);
            }

            if ('data-product-id' in $input[0]['attributes']){
                var product_id = parseInt($input[0]['attributes']['data-product-id']['value']);
                var val = $input.prop('checked')

                if(val === false){
                    $('#selectAll').prop('checked', false);
                }

            }
        });

   });
});
