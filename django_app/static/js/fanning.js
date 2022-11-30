/* fanning.js

*/

//import
/*global
csrfTOKEN : false,
set_small_button_fan,
set_small_button_fand,
isOnOwnProfile,
setupFandButtons,
console

*/
////////////////////////////                     fanning.js                  ////////////////////////////
//////////////////////////// "Fanning" functions used by the red fan buttons ////////////////////////////

(function(){

//  fan_this
//      Desc: Fans an entity (song, album, profile)
//      Args:
//          target:       string indicating what type of thing we are fanning. ('song', 'album', or 'profile' for the time being)
//          id:           int indicating object's id in the database
//          success_func: function that fires when the fanning has been done (usually this is set_small_button_fand on that particular button to change its appearance)
//      Called by: clicking on a fan button
//      Returns: nothing, but calls success_func

    function fan_this(target, id, success_func){
        $.ajax({
            type: 'POST',
            url: '/music/fan-ajax/',
            data: {
            'csrfmiddlewaretoken': csrfTOKEN,
            'unfan': 'f',
            'target': target, // This is the type of object we're fanning. Song, profile, etc.
            'id': id
            },
            success: success_func
        });
    }

//  unfan_this
//      Desc: Unfans an entity, identical to fan_this with opposite effect (above)

    function unfan_this(target, id, success_func){
        $.ajax({
            type: 'POST',
            url: '/music/fan-ajax/',
            data: {
            'csrfmiddlewaretoken': csrfTOKEN,
            'unfan': 't',
            'target': target,
            'id': id
            },
            success: success_func
        });
    }

    window.fan_this = fan_this;
    window.unfan_this = unfan_this;
}());
