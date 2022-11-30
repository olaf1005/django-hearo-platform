/* photos.js

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
createPhotoLightbox,
 */
(function(){

    function lightboxRibbon(){
        var lightbox_ribbon;
        console.log('making lightbox ribbon');
        if ($('#lightbox_ribbon').length === 0){
            lightbox_ribbon = createElem('div',{id:'lightbox_ribbon'});
            $(lightbox_ribbon).css({
                    'position' : 'absolute',
                    'width' : '195px',
                    'height' : '195px',
                    'left' : '-3px',
                    'top' : '-3px',
                    'background' : "url('/public/images/profile_corner_ribbon.png')",
                    'z-index' : '610',
                    'pointer-events' : 'none'
                });
            $(lightbox_ribbon).hide();
            $('#photo_box').append(lightbox_ribbon);
            $(lightbox_ribbon).fadeIn(1000,function(){});
        }

    }

    function closePhotoLightbox(){
        $('#darkbackground').fadeOut(300, function(){$('#darkbackground').remove();});
        window.onresize =  null;
        console.log("lightbox closed");
    }
    function recenterPhotoLightbox(){
        $('#photo_box').css({
            'margin' : '0px auto',
            'position' : 'fixed',
            'left': ($(window).width() - $('#photo_box').width()) / 2,
            'top': ($(window).height() - $('#photo_box').height()) / 2
        });
        $('#darkbackground').css({
            'width': $(window).width() + 'px',
            'height': $(document).height() + 'px'
        });
    }

    function updateCoordinates(c){
        $('#x').val(c.x);
        $('#y').val(c.y);
        $('#x2').val(c.x2);
        $('#y2').val(c.y2);
    }

    function set_profile_pic(photo_id){
        $.ajax({
            type: 'POST',
            url: '/set-profile-pic/',
            data: {
                'photo_id' : photo_id,
                'csrfmiddlewaretoken': csrfTOKEN
            },
            success: function(data){
                if (String(data) === "{}") { return -1; }
                var parsed = data;
                $('#primaryPic').attr('id','');
                $('#photo_' + photo_id + " > img").attr('id','primaryPic');
                $('#currentAccountPhoto').attr('src', '/' + parsed.thumb_photo_path);
                // setupRibbon();
                lightboxRibbon();

            }
        });
    }

    function submit_data(photo_id){
        $.ajax({
            type: 'POST',
            url: '/crop-photo/',
            data: {
                'id' : photo_id,
                'csrfmiddlewaretoken': csrfTOKEN,
                'x': $('#x').val(),
                'y': $('#y').val(),
                'x2': $('#x2').val(),
                'y2': $('#y2').val(),
                'caption': $('#captionInput').val()
            },
            success: function(data){
                if (data === "{}") { return -1; }
                var parsed = data;
                $('#photo_' + photo_id + ' img').attr('src', '/' + parsed.square_photo_path);
                if (parsed.isPrimaryPhoto){
                    $('#currentAccountPhoto').attr('src', '/' + parsed.thumb_photo_path);
                }
            }
        });
    }

    function populatePhotoLightbox(photo_id,photo_path,x,y,x2,y2, width, height, caption){
        var top_margin, curr_pic;
        top_margin = createElem('div');
        $(top_margin).css('height',10);
        $('#photo_box').append(top_margin);
        curr_pic = createElem('img', {id: photo_id, src: photo_path});
        $('#photo_box').append(curr_pic);

        $(curr_pic).Jcrop({
            aspectRatio : 1,
            bgOpacity : 0.7,
            minSize : [160,160],
            trueSize : [width, height],
            onChange : updateCoordinates,
            onSelect : updateCoordinates,
            setSelect : [x, y, x2, y2]
        });

        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'x'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'y'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'x2'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'y2'}));
        $('#photo_box').append(createElem('br'));

        $('#photo_box').append(createElem('input',{'type':'submit', id: 'set_profile_pic', className:'bttn--size-small bttn--color-green','value':'Set as profile picture'}));
        $('#photo_box').append(createElem('input', {'type' : 'text',id: 'captionInput', 'value': caption, placeholder : "Write a caption..."}));
        $('#photo_box').append(createElem('span', {id: 'someSpace'}));
        $('#photo_box').append(createElem('input',{'type':'submit', id: 'submit_crop', className:'bttn--size-small bttn--color-green','value':'Submit'}));

        //$('#darkbackground').append(lowerDiv);
        $('#submit_crop').click(function(){
            submit_data(photo_id);
            closePhotoLightbox();
        });
        $('#set_profile_pic').click(function(){
            set_profile_pic(photo_id);
        });
    }

    function nextPhoto(){}
    function prevPhoto(){}

    function createPhotoLightbox(photo_id){
        $.ajax({
            type: 'GET',
            url: '/get-photo-details/',
            data: {
                id : photo_id
            },
            success: function(data){
                if (data === "{}") { return -1; }
                var darkbackground, photo_box, parsed, x, y, x2, y2, width_prof, height_prof, photo_path, width, height, caption, isProfilePhoto;
                parsed = data;
                photo_path = parsed.photo_path;
                x = parsed.x;
                y = parsed.y;
                x2 = parsed.x2;
                y2 = parsed.y2;
                width = parsed.width;
                height = parsed.height;
                width_prof = parsed.width_prof;
                height_prof = parsed.height_prof;
                caption = parsed.caption;
                darkbackground = createElem('div', { id: 'darkbackground' , align: 'center'});
                $(darkbackground).css({
                    'width': $(document).width() + 'px',
                    'height': $(document).height() + 'px'
                }).click(function(){
                    closePhotoLightbox();
                });

                photo_box = createElem('div',{id:'photo_box'} );
                $(photo_box).css('width', width_prof + 20);
                $(photo_box).css('height', height_prof);
                $(photo_box).click(function(e){
                    e.stopPropagation();
                });
                window.onresize = function(){
                    recenterPhotoLightbox();
                };

                $(darkbackground).append(photo_box);
                $('body').append(darkbackground);
                populatePhotoLightbox(photo_id,photo_path,x,y,x2,y2, width, height, caption);
                recenterPhotoLightbox();

                $('#x').val(x);
                $('#y').val(y);
                $('#x2').val(x2);
                $('#y2').val(y2);

                if (parsed.isProfilePhoto){
                    lightboxRibbon();
                }

            }
        });
    }




    window.createPhotoLightbox = createPhotoLightbox;
    window.nextPhoto = nextPhoto;
    window.prevPhoto = prevPhoto;
    window.closePhotoLightbox = closePhotoLightbox;
}());
