$(document).ready(function () {
    $( "#birthdate" ).datepicker({
        inline: true
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