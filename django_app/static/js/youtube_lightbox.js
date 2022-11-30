/* events.js
   
 */

//import
/*global
console,
getChecked,
className,
small_fan_button,
refreshEvents,
fan_this,
editEventAjax,
unfan_this,
changeLocation,
showAjaxLoader,
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
    
    function closeVideoLightbox(){
        $('#darkbackground').remove();
        window.onresize =  null;   
        console.log("lightbox closed");
    }

    function recenterVideoLightbox(){
        $('#video_box').css({
            'left': ($(window).width() - 600) / 2,
            'top': ($(window).height() - $('#video_box').height()) / 2
        });
        $('#darkbackground').css({
            'width': $(window).width() + 'px',
            'height': $(document).height() + 'px'
        });
    }

    function populateVideoLightbox(video_id){
        var vidFrame,src;
        src = "//www.youtube.com/embed/" + video_id;
        console.log(src);
        $('#video_box').append(createElem('iframe', {'class': 'youtube-player', type: 'text/html', 'width': '640', 'height': '385', 'src': src, 'frmeborder' : '0'}));
    }


    function createVideoLightbox(video_id){
        var darkbackground,video_box;
        darkbackground = createElem('div', { id: 'darkbackground' , align: 'center'});
        $(darkbackground).css({
            'width': $(document).width() + 'px',
            'height': $(document).height() + 'px'
        }).click(function(){
            closeVideoLightbox();
        });
        video_box = createElem('div',{id:'video_box'} );
        $(video_box).css('width', 660);
        $(video_box).css('height', 394);
        $(video_box).click(function(e){
            e.stopPropagation();
        });
        window.onresize = function(){
            recenterVideoLightbox();
        };

        $(darkbackground).append(video_box);
        $('body').append(darkbackground);
        populateVideoLightbox(video_id);
        recenterVideoLightbox();
    }

    window.createVideoLightbox = createVideoLightbox;
    window.closeVideoLightbox = closeVideoLightbox;

}());
