(function($) {
    $(document).ready(function(event) {
      // not sure if there's a better way to do this, all things considered
      $radios = $('input[name$="tabular-radio"]');
      if ($radios.length === 2) {  // one real row and one template
        $radios.first().prop('checked', true);
      }
    });
    $(document).on('formset:added', function(event, $row, formsetName) {
       if ('personas' === formsetName) {
         $row.find('input[name$="tabular-radio"]').val($row.prop('id'));
       }
    });
    $(document).on('formset:removed', function(event, $row, formsetName) {
       if ('personas' === formsetName) {
         $radio = $row.find('input[name$="tabular-radio"]');
         if ($radio.prop('checked')) {
           $('input[name="' + $radio.prop('name') + '"]')
             .first()
             .prop('checked', true);
         }
       }
    });
})(django.jQuery);
