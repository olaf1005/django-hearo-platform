/* banner_crop.js

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
    function closeBannerLightbox(base64){
        $('#darkbackground').fadeOut(300, function(){$('#darkbackground').remove();});
        window.onresize =  null;
        //console.log("lightbox closed");
        if (base64 !== undefined){ /* Only when crop was finalized in ligthtbox */
          /* Have to set it as attr style as opposed to css({background: base64}) */
          /* I don't know why but one works and the other doesn't. */
          $('div.choice#custom_banner').attr('style', 'background: ' + base64);
        }
    }
    function recenterBannerLightbox(){
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
        // $('#photo_box').css({
        //     'left': ($(window).width() - 600) / 2,
        //     'top': ($(window).height() - $('#photo_box').height()) / 2
        // });
        // $('#darkbackground').css({
        //     'width': $(window).width() + 'px',
        //     'height': $(document).height() + 'px'
        // });
    }

    function updateCoordinates(c){
        $('#x').val(c.x);
        $('#y').val(c.y);
        $('#x2').val(c.x2);
        $('#y2').val(c.y2);
    }

    function submit_data(){
        $.ajax({
            type: 'POST',
            url: '/crop-banner/',
            data: {
                'csrfmiddlewaretoken': csrfTOKEN,
                'x': $('#x').val(),
                'y': $('#y').val(),
                'x2': $('#x2').val(),
                'y2': $('#y2').val()
            },
            success: function(data){
                closeBannerLightbox(data);
            }
        });
    }

    function populateBannerLightbox(photo_path,x,y, x2, y2, width_true, height_true, width_resized, height_resized){
        var top_margin, curr_pic, captionBox;
        top_margin = createElem('div');
        $(top_margin).css('height',10);
        $('#photo_box').append(top_margin);
        curr_pic = createElem('img', {id: 'banner_img', src: photo_path});
        $('#photo_box').append(curr_pic);

        $(curr_pic).Jcrop({
            aspectRatio : 6.0,
            bgOpacity : 0.7,
            minSize : [160,160],
            trueSize : [width_true, height_true],
            onChange : updateCoordinates,
            onSelect : updateCoordinates,
            setSelect : [x, y, x2, y2]
        });

        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'x'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'y'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'x2'}));
        $('#photo_box').append(createElem('input', {'type' : 'hidden',id: 'y2'}));
        $('#photo_box').append(createElem('br'));
        $('#photo_box').append(createElem('input',{'type':'submit', id: 'cancel_crop', className:'bttn--size-small bttn--color-green','value':'Cancel'}));
        $('#photo_box').append(createElem('input',{'type':'submit', id: 'submit_crop', className:'bttn--size-small bttn--color-green','value':'Upload'}));
        $('#submit_crop').click(function(){
            submit_data();
        });
        $('#cancel_crop').one('click', function(){
            closeBannerUploadLightbox();
        });
    }

    function createBannerLightbox(){
        var photo_path,x,y, x2, y2, width_true, height_true, width_resized, height_resized, darkbackground, photo_box;
        $.ajax({
            type: 'GET',
            url: '/my-account/get-banner-data/',
            data: {},
            success: function(data){
                if (data === "{}") { return -1; }
                var parsed = data;
                photo_path = parsed.path;
                x = parsed.crop_left;
                y = parsed.crop_top;
                x2 = parsed.crop_right;
                y2 = parsed.crop_bottom;
                width_true = parsed.texture_width;
                height_true = parsed.texture_height;
                width_resized = parsed.texture_resized_width;
                height_resized = parsed.texture_resized_height;

                darkbackground = createElem('div', { id: 'darkbackground' , align: 'center'});
                $(darkbackground).css({
                    'width': $(document).width() + 'px',
                    'height': $(document).height() + 'px'
                }).click(function(){
                    closeBannerLightbox();
                });
                photo_box = createElem('div',{id:'photo_box'} );
                $(photo_box).css('width', 500);
                $(photo_box).css('height', 500);
                $(photo_box).css('padding-bottom', 0);
                $(photo_box).click(function(e){
                    e.stopPropagation();
                });
                window.onresize = function(){
                    recenterBannerLightbox();
                };

                $(darkbackground).append(photo_box);
                $(darkbackground).hide();
                $('body').append(darkbackground);
                $(darkbackground).fadeIn();
                populateBannerLightbox(photo_path,x,y,x2,y2,width_true, height_true, width_resized, height_resized);
                $(photo_box).css('width', width_resized + 20);
                $(photo_box).css('height', height_resized + 20);
                recenterBannerLightbox();
                    }
                });
    }

    window.createBannerLightbox = createBannerLightbox;
    window.closeBannerLightbox = closeBannerLightbox;

}());
