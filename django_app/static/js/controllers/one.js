/*
  Hearo One controller

  Instantiates map, listings, and filters view
  and brokers events between them
*/

hearo.setup.one = function () {
  hearo.map        = new hearo.views.Map()
  hearo.listings   = new hearo.views.Listings()
};
