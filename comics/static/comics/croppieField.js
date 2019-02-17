(function ($) {
  var croppies = {}
  window.croppies = croppies;

  function getCroppie(id) {
    return croppies[id] || (croppies[id] = new Croppie(
      $('#'+id+' .cf-croppie-area').get(0),
      {
        viewport: {
          width: 100,
          height: 100,
          type: 'circle'
        },
        showZoomer: false,
      }
    ));
  }

  function destroyCroppie(id) {
    if (croppies[id]) {
      croppies[id].destroy();
      delete croppies[id];
    }
  }

  function load(id) {
    try {
      return JSON.parse($('#'+id+' input[name$="_crop"]').val());
    } catch (e) {}
  }

  function save(id) {
    $('#'+id+' input[name$="_crop"]')
      .val(JSON.stringify(croppies[id].get()));
  }

  function edit(id, data) {
    if (data) {
      $('#'+id).removeClass('locked').addClass('editing');
      getCroppie(id).bind(data);
    }
  }

  function readFile(id, ignoreApiCheck) {
    var input = $('#'+id+' input[type=file]').get(0);
    if (input.files && input.files[0]) {
      var reader = new FileReader();

      reader.onload = function (e) {
        var data = { url: e.target.result };
        // restore old zoom unless data is initial
        var oldData = load(id);
        if (oldData && oldData.zoom) {
          data = Object.assign(oldData, data);
        }
        edit(id, data);
      }

      reader.readAsDataURL(input.files[0]);
    } else if (!ignoreApiCheck) {
      alert('Sorry - you\'re browser doesn\'t support the FileReader API');
    }
  }

  function readJson(id) {
    edit(id, load(id));
  }

  $(document).ready(function (event) {
    $('.cf-container')
      .find('input[type=file]')
      .on('change', function () {
        //
        readFile($(this).closest('.cf-container').prop('id'), this);
      })

    $('form').submit(function () {
      for (var id in Object.keys(croppies)) {
        save(id);
      }
    })

    $('.cf-container input[type=button]')
      .on('click', function () {
        var $target = $(this);
        var $cntr = $target.closest('.cf-container');
        var id = $cntr.prop('id');
        if ($target.hasClass('cf-cancel')) {
          $cntr.removeClass('editing');
          if ($cntr.find('input[name$="_crop"]').val()) {
            $cntr.addClass('locked');
          }
          destroyCroppie(id);
        } else if ($target.hasClass('cf-clear')) {
          $cntr
            .removeClass('initial editing locked')
            .find('.cf-preview')
            .css('background-image', 'none')
            .find('.cf-upload input')
            .val('')
        } else if ($target.hasClass('cf-lock')) {
          getCroppie(id)
            .result({
              type: 'canvas',
              size: {
                width: 50,
                height: 50,
              },
              circle: false,
            })
            .then(function (resp) {
              save(id);
              $cntr
                .removeClass('initial editing')
                .addClass('locked')
                .find('.cf-preview')
                .css('background-image', 'url('+resp+')')
              destroyCroppie(id);
            })
        }
      })

    $('.cf-preview')
      .on('click', function () {
        // NOTE: couldn't easily make editing the original work on the server
        var $cntr = $(this).closest('.cf-container');
        if ($cntr.hasClass('locked') && !$cntr.hasClass('initial')) {
          readFile($cntr.prop('id'));
        }
      })
  })

})(django.jQuery)
