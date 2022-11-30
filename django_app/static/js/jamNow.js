/* jamNow.js

*/

//import
/*global
createElem,
console,
typeDropdown,
csrfTOKEN,
profileID,
jamLever:true,
appendNewJamData,
getJamData,
setupLinks,
recursivePreload,
setupFanButtons,
setupFandButtons,
type_dropdown,
setupTooltips,
categories_slider,
refresh_directory,
userTab,
autocompleteAll,
*/

(function(){

    var infinite_search, directoryCategory, inAjaxCall = false, category;
    infinite_search = true; // Whether we can use infinite scrolling
    /*
        Becomes helpful because allows us to wait for ajax call before
        another infinite scrolling callback
    */

    /*
        filter_dropdown
        Desc: Custom dropdown list built for hearo. Acts like a regular dropdown list with these exceptions:
            - Opens on hover, not on click
            - Selection accompanied by x button which clears the selection and opens the dropdown
            - Contents change based on the slider at the top of the jam page
            - Has a default category name in grey that is covered by a selection
        Args:
            name:   the grey category name that shows up when no selection is made (cleared when selection made)
            action: function fired when selection is made (right now this is refresh_directory)
        Called by: setupJam()
        Returns: nothing
    */

    /* OUT OF DATE: will soon be re-written as a jQuery plugin on a <ul> element */

    function filter_dropdown(name, action){
        var i, li_obj, width, me = this;
        this.name = name;
        this.items = [];
        this.all = createElem('div', {id: name + '_dropdown_all'});
        this.button = createElem('div', {className: 'dropdown_button', id:name}, this.name);
        if(width){$(this.button).css('width',width);}
        this.open = false;
        this.li_objs = [];
        this.arm_close = false;
        this.selection = null;
        this.action = action;

        for (i = 0; i < this.items.length; i += 1){ // Make list items
            li_obj = createElem('li', {}, this.items[i]);
            this.li_objs.push(li_obj);
            $(this.all).append(li_obj);
            $(li_obj).hide();
        }

        $(this.button).unbind().mouseover(function(){
            //I want this to dropdown no matter what. Keep operation consistent
            //-charlie
            me.arm_close = false;
            me.open_list();
        }).mouseout(function(){
            me.arm_close = true;
            setTimeout(function(){
                if (me.arm_close){
                    me.close(false);
                }
            }, 200);
        }).click(function(){
            if (me.selection){
                me.clear();
                me.open_list();
            }
        });

        $(this.all).append(this.button).mouseover(function(){
            me.arm_close = false;
        }).mouseout(function(){
            me.arm_close = true;
            setTimeout(function(){
                if (me.arm_close){
                    me.close(false); // DON'T UPDATE IT
                }
            }, 500);
        });

        return this;
    }

    filter_dropdown.prototype.open_list = function(){
        var li, me = this;
        for (li in this.li_objs){
            $(this.li_objs[li]).show().unbind().click(function(){
                me.select_opt($(this).text());
                me.close(false); // UPDATE IT
            });
        }
    }

    //y is if we are selecting something
    filter_dropdown.prototype.close = function(y){
        var do_action;
        if (y == undefined){
            y = true;
        }
        this.open = false;
        for (var li in this.li_objs){
            $(this.li_objs[li]).hide()
        }
        if (this.selection == null && y){
            console.log('closed');
            this.action(null, category);
        }
    }

    filter_dropdown.prototype.select_opt = function(opt){
        this.selection = opt;
        this.button.className = 'dropdown_selection';
        this.button.innerHTML = opt;
        this.action(null, category);
    }

    filter_dropdown.prototype.set_items = function(items){
        this.category = category;
        this.clear(false);
        this.items = items;
        this.close(false);
        for (var li in this.li_objs){
            $(this.li_objs[li]).remove();
        }
        for (var i in this.items){
            var li_obj = createElem('li', {}, this.items[i]);
            this.li_objs.push(li_obj);
            $(this.all).append(li_obj);
            $(li_obj).hide();
        }
    }

    filter_dropdown.prototype.clear = function(y){ // reset after clearing a selection, so another can be selected.
        var do_action;
        if (y == undefined){
            do_action = true;
        } else {
            do_action = false;
        }

        // $('#browsing_type').text(categories_slider.selected);

        this.button.className = 'dropdown_button';
        this.button.innerHTML = this.name;
        this.selection = null;
        if (do_action){
            this.action(null, category); // UPDATE IT when we clear it.
        }
    }

    /*
        setupJam
            Desc: this initializes the jam filter objects and the rest of the page on $(document).ready()
            Called by: $(document).ready() on the jam page
            Returns: nothing
    */

    setupJam = function(){
        $('#onair_button').click(function(){
            onair_filter( $(this).attr('state') ); // Toggle Jam page based on the OnAir switch
        });

        type_dropdown = new filter_dropdown('Type', refresh_directory);

        $('.filter_module').first().find('.controls').append(type_dropdown.all);

        $("#maxDist").change(function() {
            $("#maxDistForm").submit()
        });

        $('#jam_filter').click(refresh_directory);
        $('#filters').find('input').keyup(function(){
          if ($(this).val() === ''){
            refresh_directory();
          }
        }).enter(refresh_directory);

        autocompleteAll({
            '#Genres' : 'genres',
            '#Instrument' : 'instruments',
            '#Location' : 'locations'
        });

        /* Initialize earl on the People/Groups selection */
        $('#slider').earl({
          callbacks: {
            select: refresh_directory
          }
        });

        $(window).endlessScroll({
            bottomPixels:      500,
            intervalFrequency: 1000,
            fireOnce:          true,
            fireDelay:         0,
            loader:            '',
            ceaseFire: function(page){
                if ($('#wrapper.infinite_scrolling').length < 1){
                  return true;
                } else {
                  return false;
                }
            },
            resetCounter: function(page) { return; },
            callback: function(page){
                if (infinite_search) {
                    infinite_search = false;
                    getJamData(appendNewJamData, 't');
                }
            }
        });
    }

    /*
      refresh_directory
          Desc: Makes an AJAX call with parameters derived from the filter objects on the jam page
                and rebuilds the jam page's list with the data that is returned.
          Args:
              name: The grey category name that shows up when no selection is made (cleared when selection made)
              action: function fired when selection is made (right now this is refresh_directory)
          Called by: $(document).ready() on the jam page
          Returns: nothing
    */

     refresh_directory = function($this, cat){
        category = cat; /* Save the category */
        var $wrapper = $('#jam_directory');
        $wrapper.find('.jam_listing').remove();
        $wrapper.find('.loader').show();
        $("#no_results").hide();
        getJamData(appendNewJamData, true);
    }

    function getJamData(success, more){
        if (inAjaxCall){
          console.log('inajaxcall');
          return;
        }

        var start, type, location, instrument, genre, onair, loader, category = $('#slider').attr('value');

        type = type_dropdown.selection;
        if (category !== type_dropdown.category){
          type_dropdown.set_items({
            'People': ['All People', 'Musicians', 'Fans', 'Teachers','Producers'],
            'Groups': ['All Groups','Bands', 'Venues']
          }[category], category);
        }

        $('#browsing_type').text(type);

        /* Get search values */
        location = $('#Location').val();
        instrument = $('#Instrument').val();
        genre = $('#Genre').val();

        start = $('.jam_listing').length;
        inAjaxCall = true;
        $.ajax({
            url: '/directory/load-directory',
            data: {
              start: start,
              category: category,
              type: type,
              location: location,
              instrument: instrument,
              genre: genre,
              onair: onair
            },
            success: function(data){
                success(data);
                inAjaxCall = false;
            },
            error:function(data){
                console.log(data);
                infinite_search=false;
            }
        });
    }

    function appendNewJamData(data){
        $(".loader").hide();
        if($('#wrapper.infinite_scrolling').length < 1){return ;}
        var parsed = $.parseJSON(data);
        $("#directory_label").html(parsed[0]);
        if(parsed[1].trim()){
            $("#no_results").hide();
            $("#jam_directory").append(parsed[1]);
            setupLinks();
            setupFanButtons();
            setupFandButtons();
            setupTooltips();
            if($("#topContainer").height() + $("#jam_directory").height() < $(window).height()){
                getJamData(appendNewJamData,'t');
            }
        }else if($(".jam_listing").length == 0){
            $("#no_results").show();
        }
        infinite_search = true;
        //$('button.fan, button.unfan').each(function(){ $(this).fanbutton() });
    }


window.setupJam = setupJam;
window.filter_dropdown = filter_dropdown;
window.directoryCategory = directoryCategory;

// This will be defined l8r
window.type_dropdown = null;

window.g = getJamData;
window.a = appendNewJamData;

}());
