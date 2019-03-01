(function ($) {
  var croppies = {};

  function getViewport(id) {
    var $display = $('#'+id+'-display');
    var dims =[$display.width(), $display.height()];
    var u = dims[1] > dims[0] ? 1 : 0;
    var l = dims[1] < dims[0] ? 1 : 0;
    var ratio = dims[u] / dims[l];

    if (dims[l] < 100)  {
      ratio = 100 / dims[l];
      if (dims[u] * ratio > 300) {
        ratio = 300 / dims[u];
      }
    } else if (ratio >= 1.5) {
      ratio = 300 / dims[u];
    } else {
      ratio = 2 * 220 / (dims[u] + dims[l]);
    }

    return Object.assign({
      width: dims[0] * ratio,
      height: dims[1] * ratio,
    }, $('#'+id+'-croppie').data('viewport'))
  }

  function getCroppie(id) {
    if (!croppies[id]) {
      croppies[id] = new Croppie(
        $('#'+id+'-croppie').get(0),
        {
          viewport: getViewport(id),
          boundary: {
            width: 300,
            height: 300,
          },
          showZoomer: true,
        }
      );
    }
    return croppies[id];
  }

  function destroyCroppie(id) {
    if (croppies[id]) {
      croppies[id].destroy();
      delete croppies[id];
    }
  }

  function show(id) {
    getCroppie(id);
    MicroModal.show(id+'-modal');
  }

  function close(id) {
    // do not destroy Croppie to allow for easy editing
    MicroModal.close(id + '-modal');
  }

  function load(id) {
    try {
      return JSON.parse($('#'+id+'-crop').val());
    } catch (e) {}
  }

  function save(id) {
    $('#'+id+'-crop')
      .val(JSON.stringify(croppies[id].get()));
  }

  function readFile(id, ignoreApiCheck) {
    var input = $('#'+id+'-input').get(0);
    if (input.files && input.files[0]) {
      var reader = new FileReader();
      reader.onload = function (e) {
        var data = { url: e.target.result };
        getCroppie(id).bind(data);
      }
      reader.readAsDataURL(input.files[0]);

      destroyCroppie(id);
      show(id);
    } else if (!ignoreApiCheck) {
      alert('Sorry - you\'re browser doesn\'t support the FileReader API.');
    }
  }

  $(document).ready(function () {
    $('*[data-croppie]')
      .on('click', function (event) {
        var $target = $(event.target);
        var id = $(this).data('croppie');
        var $cntr = $('#'+id+'-widget');
        if ($target.hasClass('cf-commit')) {
          var $display = $('#'+id+'-display');
          getCroppie(id)
            .result({
              type: 'canvas',
              size: {
                width: $display.width(),
                height: $display.height()
              },
              circle: false
            })
            .then(function (resp) {
              save(id);
              $cntr
                .removeClass('blank')
                .addClass('has-value')
                .find('.cf-display')
                .css('background-image', 'url('+resp+')')
              close(id);
            })
        } else if ($target.hasClass('cf-edit')) {
          if (croppies[id]) {
            show(id);
          }
        } else if ($target.hasClass('cf-discard')) {
          destroyCroppie(id);
          $cntr
            .removeClass('has-value initial-value')
            .addClass('blank')
            .find('.cf-display')
            .css('background-image', 'none')
          $cntr
            .find('.cf-actions input')
            .val('')
        }
      })
      .find('input[type=file]')
      .on('change', function () {
        readFile($(this).closest('.cf-container').data('croppie'), this);
      })
  })

})(django.jQuery)
