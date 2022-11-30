 /*global
  hearo,
  */

(function(){
  var setup = function(){

  hearo.elements.savebutton.hide();

  function changeDownloadFormat(format){
    $.ajax({
      url    : '/my-account/change-default-download/',
      type   : 'POST',
      data   : {
        'download_type'     : format,
        csrfmiddlewaretoken : csrfTOKEN
      },
      success: function(response){
      }
    });
  }

  var music_format_dropdown = new hearo.components.Dropdown({
    el: '#music-download-format',
    no_redirect: true,
  });


  //time: $($('#time-dropdown li.dropdown-widget__option--selected')[0]).attr('val'),

  /*
   * Helper methods
   */



  /*
   * Bind event handlers
   */
  music_format_dropdown.on('change', changeDownloadFormat);



  /*
   * Other setup
   */



  /*
   * $document.ready exports
   */

  };

  /*
   * global exports
   */

  window.hearo.setup.dashboard.downloads = setup;

}());
