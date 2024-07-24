$(document).ready(function () {
    /*$( "#birthdate" ).datepicker({
        inline: true
    });*/

document.addEventListener('scroll', function(e) {
   if(window.pageYOffset === 0){
    var div = document.getElementById("oe_main_menu_navbar");
    if(div !== null){
     div.classList.remove('fixed-top')
    }
}
});

    $('.close').click(function(){
          $('.myVideoClass').each(function(){
            $(this)[0].contentWindow.postMessage('{"event":"command","func":"' + 'stopVideo' + '","args":""}', '*');

          });
        });

    $(".scrolltoform").click(function() {
        $('html, body').animate({
            scrollTop: $("#requestform").offset().top - 250
        }, 1500);
    });
});

   function getFileNameWithExt(event) {

      if (!event || !event.target || !event.target.files || event.target.files.length === 0) {
        return;
      }

      const name = event.target.files[0].name;
      const lastDot = name.lastIndexOf('.');

      const fileName = name.substring(0, lastDot);
      const ext = name.substring(lastDot + 1);

      outputfile.value = fileName;

    }

     function scrolldiv() {
        var elem = document.getElementById("requestform");
        var div = document.getElementById("oe_main_menu_navbar");
        if(div !== null){
         div.classList.add('fixed-top')
        }
        elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }