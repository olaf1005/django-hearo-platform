(function(){

 /*
  * The root global hearo, to which we'll be adding things in view-specific files
  */
  window.hearo = {
   /*
    * hearo.setup's methods are called by onready.js
    * The method fired is determined by the context div's classname
    */
    defaultTitle: "Discover new music on tune.fm",
    setup:  {
      dashboard: {}
    } // Top-level controllers
    , views:  {}
    , models: {}
    , mixins: {}
    , utils:  {}
    , elements: {} // TODO remove
    //pending_download will either be false or a DownloadCharge id
    //if not false, ask for some data from the server about the status of the download
    , pending_download : false
  };
}());
