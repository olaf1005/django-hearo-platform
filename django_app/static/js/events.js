/* events.js

 */

//import
/*global
console,
getChecked,
className,
small_fan_button,
refreshEvents,
populateEvents,
fan_this,
deleteEventAjax,
editEventAjax,
userTabGraphic,
addUserDropdown,
unfan_this,
changeLocation,
showAjaxLoader,
autocompleteAll,
hideAjaxLoader,
events_dropdown,
filter_dropdown,
createElem,
startEditingEvent,
userTab,
editEvent,
continueEventLightbox,
csrfTOKEN : false,
 */
(function(){
    function closeEventLightbox(){
        $('#darkness').remove();
        window.onresize =  null;
    }
    function resetEventLightbox(){
        $('#event_box').css({
            'left': ($(window).width() - 600) / 2,
            'margin-top': ($(window).height() - $('#event_box').height()) / 2

        });
        $('#darkness').css({
            'width': $(window).width() + 'px',
            'height': $(document).height() + 'px'
        });
    }
    function openEventLightbox(id, onProfile){
        $.get('/get-event/', {'id':id}, function(data){
            var parsed = data;
            continueEventLightbox(parsed[0], parsed[1],onProfile);
        });
    }
    function createCell(a,b,c){
        return $(createElem('td')).append(createElem(a,b,c));
    }
    function showEventLightbox(){
        var darkness,event_box;
        darkness = createElem('div', { id: 'darkness' });
        $(darkness).css({
            'width': $(document).width() + 'px',
            'height': $(document).height() + 'px'
        }).click(function(){
            closeEventLightbox();
        });

        event_box = createElem('div',{id:'event_box'});
        $(event_box).click(function(e){
            e.stopPropagation();
        });
        window.onresize = function(){
            resetEventLightbox();
        };
        $(darkness).append(event_box);
        $('body').append(darkness);
    }
    function continueEventLightbox(event, fans, onProfile){

        var row,darkness,event_box,title,usertab,location,description,time, fan, fan_box, fan_scroll, tableholder,
        table,who,what,where,when, edit, artists, a_list, del, url, fixed_url;
        showEventLightbox();
        event_box = $("#event_box");
        darkness = $("#darkness");
        $(event_box).append(createElem('h4',{'id':'header'}, 'event details'));


        title = createElem('h4',{'id':'event_title'},event.title);

        if (event.logged_in){
            fan = small_fan_button(event.fanned, "event",event.id);
        }
        if(event.ticket_url.indexOf('http://') !== 0){
            fixed_url = 'http://' + event.ticket_url;
        }
        else{
            fixed_url = event.ticket_url;
        }

        if (event.logged_in){
            if(fixed_url !== "http://"){
                //console.log(fixed_url);
                url = $(createElem('a-external',{'href':fixed_url, 'id':'tix_pic'})).text('TIX');
                $(event_box).append(url);


                //wrapInner('<img src="/public/images/tix.png" />')
            }
        }
        $(event_box).prepend(fan);

        table = $(createElem('table')).addClass('event_view_table');
        tableholder = $(createElem('div',{className:'inset_box'})).addClass('edit_event_inset_box');
        tableholder.append(table);

        who = $(createElem('tr'));
        who.append(createCell('span',{className:'event_desc'},'Host: '));
        who.append( $(createElem('td')).append(new userTab(event.profile.name, event.profile.img_path, event.profile.url)));
        table.append(who);
        if(event.description){
            what = $(createElem('tr')).append(createCell('span',{className:'event_desc'},"What: "));
            what.append(createCell('div',{'id':'event_description'},event.description));
            table.append(what);
        }
        if(event.location || event.location_text){
            where = $(createElem('tr')).append(createCell('span',{className:'event_desc'},'Where: '));
            where.append(createCell('span',{'id':'event_location'},event.location));

            where.find('#event_location').after($(createElem('div'))
                .append(createElem('span',{'id':'event_location_text'},event.location_text)));
            table.append(where);
        }


        when = $(createElem('tr')).append(createCell('span',{className:'event_desc'},'When: '));
        when.append(createCell('span',{'id':'event_starts'},event.s_string));

        when.find('#event_starts').after(createElem('span',{'id':'event_ends'},' - '+event.e_string));

        table.append(when);

        if(event.artists.length > 0){

            artists = $(createElem('tr')).append(createCell('span',{className:'event_desc'}, 'Featuring: '));
            a_list = createCell('div',{'id':'artists_listing'});
            $.each(event.artists,function(){
                $(a_list).append(new userTab(this.name, this.img_path, this.url));
            });
            artists.append(a_list);
            table.append(artists);
        }

        fan_box = createElem('div',{className:'box','id':'event_fans'});
        $(fan_box).append(createElem('h4',{'id':'fan_num'}, fans.length + " fans"));

        fan_scroll = createElem('div',{className:'scrollbox'});
        $.each(fans, function(i, fan){
            $(fan_scroll).append(new userTab(fan.name, fan.img_path, fan.url));
        });
        $(fan_box).append(fan_scroll);

        $(event_box).append(title)
            .append(tableholder)
            .append(fan_box);

        if(event.mine){
            row = $(createElem('div',{'id':'event_button_row'}));
            edit = $(createElem('input',{'type':'submit',className:'big-green','value':'Edit'}))
                .click(function(){startEditingEvent(event.id, onProfile);});

            del = $(createElem('input',{'type':'submit',className:'big-red','value':'Delete'}))
                .click(function(){
                    deleteEventAjax(event.id, onProfile);
                    closeEventLightbox();
                });
            row.append(del);
            row.append(edit);
            $(event_box).append(row);
        }


        resetEventLightbox();

    }

    //converts the event lightbox into an editing interface
    function startEditingEvent(id, onProfile){
        $.get('/get-event/',{'id':id},function(data){
            var e = data[0];
            if(id === -1) {editEvent(0, e.profile,onProfile);}
            else {editEvent(e, e.profile,onProfile);}
        });
    }
    function editEvent(event, profile,onProfile){
        var a_list, add_artists, artists, row, cancel, del, id,table, title, description, location, location_text, starts, ends, save,check, tableholder, ticket_url;
        if(event){
            title= event.title;
            description = event.description;
            location = event.location;
            location_text = event.location_text;
            starts = event.form_starts;
            ends = event.form_ends;
            id = event.id;
            a_list = event.artists;
            ticket_url = event.ticket_url;
        }
        else{
            id="";title = ""; description="";location_text="";location="";starts="";ends="";ticket_url="";
            a_list = false;
        }
        if($("#event_box").length >0){
            $("#event_box").empty();
        }
        else{
            showEventLightbox(); //will create a new lightbox for the new event
        }

        $("#event_box").addClass('editing_event_box')
            .append(createElem('h4',{'id':'header'}, 'edit your event!'));
        table = $(createElem('table')).css({'margin-left':'39px'});
        $("#event_box").append(table);
        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Title: '))
            .append(createCell('input',{'type':'text','id':'event_title_input'})));
        $("#event_title_input").val(title);


        check = $(createElem('label',{'id':'check'}));

        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Location: '))
            .append($(createElem('td'))
                .append(check)
                .append($(createElem('input',{'id':'id_city','type':'text'}))
            .after($(createElem('div',{'id':'choices'}))
                .css('display','none')))));
        if(location){
            check.text('Checked').css('background', 'rgba(0,100,0,.8)');
            $("#id_city").val(location);
        }
        else if(profile.location){
            $("#id_city").val(profile.location);
            check.text('Checked').css('background', 'rgba(0,100,0,.8)');
        }
        else{
            check.text('Check It').css('background', 'rgba(100,0,0,.8)');
        }
        check.css('cursor','pointer').click(function(){changeLocation();});

        $('#id_city').keydown(function(){
            $('#check').text('Check It');
            $('#check').css('background','rgba(100,0,0,.8)');
        }).focusout(function(){changeLocation();});

        //description stuff
        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Description: '))
            .append(createCell('textarea',{'id':'event_description_input'})));
        $("#event_description_input").val(description);


        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Starts: '))
            .append(createCell('input',{'id':'event_start_input','type':'text'})));
        $("#event_start_input").val(starts);
        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Ends: '))
            .append(createCell('input',{'id':'event_end_input','type':'text'})));
        $("#event_end_input").val(ends);
        $('#event_start_input').datetimepicker({ dateFormat: 'yy-mm-dd', timeFormat: 'hh:mm', ampm: true });
        $('#event_end_input').datetimepicker({ dateFormat: 'yy-mm-dd', timeFormat: 'hh:mm', ampm: true});

        //ticket url
        table.append($(createElem('tr'))
            .append(createCell('span',{className:'event_desc'},'Ticket URL:'))
            .append($(createElem('input',{'id':'event_ticket_url','type':'text'}))));
        $('#event_ticket_url').val(ticket_url);


        save = $(createElem('input',{'type':'submit',className:'big-green','value':'Save'}))
            .click(function(){
                var title,start = $("#event_start_input");
                title= $("#event_title_input");
                $('.error').parent().remove();
                if(! start.val()){
                    start.parent().after(createCell('span',{className:'error'},'*required*'));
                }
                if(! title.val()){
                    title.parent().after(createCell('span',{className:'error'},'*required*'));
                }
                if(title.val() && start.val()){
                    editEventAjax(id,onProfile);
                    closeEventLightbox();
                }
        });

        cancel = $(createElem('input', {'type':'submit',className:'big-red','value':'Cancel'}))
            .click(function(){
                closeEventLightbox();
            });

        row = $(createElem('div',{'id':'event_button_row'}));
        row.append(cancel).append(save);
        add_artists = $(createElem('div',{'id':'add_artists',className:'inset_box'}))
            .append(createElem('h4',{},'who\'s playing?'))
            .append($(createElem('input',{'type':'text','id':'user_search', className:'enter name(s)'})).pretty_input({'attr':'class'}))
            .append(createElem('div',{className:'scrollbox'}));

        artists = $(createElem('div',{'id':'artists',className:'inset_box'}))
            .append(createElem('h4',{},'Artists'))
            .append(createElem('div',{className:'scrollbox'}));

        if(a_list){
            $.each(a_list,function(){
                var u = new userTabGraphic(this.name,this.img_path,this.url,this.id);
                artists.find('.scrollbox').append($(createElem('div',{className:'user_row'}))
                    .append(u));
                $(u).click(function(){$(this).parent().remove();});
            });
        }else{
            artists.css('display','none');
        }


        $("#event_box")
            .append($(createElem('div',{'id':'search_container'}))
                .append(add_artists)
                .append(artists))
            .append(row);

        // TODO: replace with this with autocomplete
        addUserDropdown($("#user_search"), $("#add_artists .scrollbox"),
            function(){
                $("#event_box #artists").show()
                    .find('.scrollbox').append($(this).parent());
                $(this).unbind('click').click(function(){
                    $(this).parent().remove();
                });
            },
            "/search/get-artists",{'eventid':id},
            $("#artists .scrollbox"));

        resetEventLightbox();

    }
    function deleteEventAjax(id, onProfile){
        $.ajax({
            url : '/delete-event-ajax/',
            type : 'POST',
            data : {'id' : id, 'csrfmiddlewaretoken': csrfTOKEN},
            success: function(){
                if(onProfile==="t"){
                    $.get('/get-profile-events', function(data){
                        var events = data;
                        populateEvents(events,onProfile);
                    });
                }
                else{refreshEvents();}
            }
        });
    }
    /*
        after checking to make sure the event is well formed (as isEventFormed())
        calls ajax to edit_event_ajax in events.views.py which creates or edits
        the event depending on whether it already exists
            displays an error message if there is an error
            else success message is shown
    */
    function editEventAjax(id, onProfile){//id is the id of the event
        if($("#event_title_input").val() !== "" && $("#event_start_input").val() !== ""){
            var artists,title,start,end,loctext,loc,desc,del;
            title = $("#event_title_input").val();


            artists = $("#artists .scrollbox").children().children().toArray().map(function(ob){return $(ob).attr('id');});

            $.ajax({
                type: 'POST',
                url: '/shows/edit-event-ajax/',
                data: {
                    'id' : id,
                    'csrfmiddlewaretoken': csrfTOKEN,
                    'title': title,
                    'starts': $("#event_start_input").val(),
                    'ends': $("#event_end_input").val(),
                    'elocation' : $("#id_city").val(),
                    'description': $("#event_description_input").val(),
                    'artists' : JSON.stringify(artists),
                    'ticket_url'  : $("#event_ticket_url").val()
                },
                success: function(){
                    if(onProfile==="t"){
                        $.get('/get-profile-events', function(data){
                            var events = data;
                            populateEvents(events,onProfile);
                        });
                    }
                    else{refreshEvents();}
                }
            });
        }
    }
    function setupCalendar(){
        $('#calendar').fullCalendar({
            header: {
                left: 'today prev,next',
                center: 'title',
                right: 'month basicWeek'

                },
            /*
            loading: function(isLoading, view){
                if(isLoading){
                    showAjaxLoader();
                    var a = 1;
                }
                else{
                    hideAjaxLoader();
                }
            },*/
            eventSources: [
            ],
            eventClick: function(calEvent, jsEvent, view) {
                openEventLightbox(calEvent.id);
            },
            eventMouseover : function(event , jsEvent, view){
                $(this).css('cursor', 'pointer');
            }
        });
    }
    function populateEvents(data, onProfile){
        var scrollbox, empty,text;
        if(onProfile === "t"){scrollbox =  $("#events .scrollbox");}
        else{ scrollbox = $("#callist .scrollbox");}

        scrollbox.empty();
        if(data.length === 0 ){
            if(onProfile === 't'){text = "You don't have any events";}
            else{text = 'No shows selected';}
            empty = $(createElem('div',{className:'empty_media'},text));
            if(onProfile === 't'){
                $(empty).addClass('no_shows_selected_profile');
            }
            else{
                $(empty).addClass('no_shows_selected');
            }
            empty.append(createElem('br'));
            if(onProfile === 't'){
                empty.append($(createElem('span',{},"Create one"))
                    .click(function(){startEditingEvent(-1,onProfile);})
                    .append(createElem('div',{className:'continue_arrow'})));
            }
            scrollbox.append(empty);
        }
        $.each(data, function(i,event){
            var event_div, cal_div = $(createElem('div',{className:'cal'}))
                .append(createElem('h2',{},event.short_month))
                .append(createElem('h1',{},event.day));

            event_div = $(createElem('div',{className:'event'}))
                .click(function(){openEventLightbox(event.id,onProfile);})
                .append(cal_div)
                .append($(createElem('div',{className:'event_info'}))
                    .append(createElem('h3',{className:'ellipsis'},event.title))
                    .append(createElem('h5',{className:'ellipsis'},event.location)));
            scrollbox.append(event_div);
        });
    }
    function refreshEvents(){
        $(".fc-button-next .fc-button-content").text('>>');
        $(".fc-button-prev .fc-button-content").text('<<');
        $("#calendar").fullCalendar('removeEventSource',
            '/shows/update/'
        );
        $("#calendar").fullCalendar('addEventSource',
            {
                url : '/shows/update/',
                type : 'GET',
                data : {
                    'filter': events_dropdown.selection || 'All Events',
                    'location' : $("#Location").val() === 'Location' ? '' : $("#Location").val()
                },
                success: populateEvents
            }
        );
    }
    function setupEvents(logged_in){

        window.events_dropdown = new filter_dropdown('All Events', function(){ refreshEvents(); }, 150);
        $('#events_filter_module').append(events_dropdown.all);
        if(logged_in){ events_dropdown.set_items(['All Events','Fan Events']); }
        else         { events_dropdown.set_items(['All Events']); }
        var loc = $("#Location");
        loc.pretty_input({'attr':'id'});
        if(loc.attr('name')){
            loc.val(loc.attr('name'))
               .removeClass('grey');
        }

        $('#filter-events').click(function() { refreshEvents();});
        setupCalendar();
        refreshEvents();
        autocompleteAll({ "#Location"  : 'locations'});
    }

    //export here
    window.editEventAjax = editEventAjax;
    window.openEventLightbox = openEventLightbox;
    window.closeEventLightbox = closeEventLightbox;
    window.setupEvents= setupEvents;
    window.startEditingEvent = startEditingEvent;
}());
