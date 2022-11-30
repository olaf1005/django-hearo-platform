(function(){

function uploadFile(file, options) {

    var handlers = $.extend({
        success : function(percent){},
        error: function(name){},
        progress : function(name){}
    }, options);

    var uploadToS3 = function(data){
        var name = data['name']; // uuid name

        var uploadProgress = function(evt){
            if(evt.lengthComputable){
                var percent = Math.round(evt.loaded * 100 / evt.total);
                handlers.progress(percent);
            }
        };
        var uploadComplete = function(evt){
            handlers.success(name);
        }; 
        var uploadFailed = function(evt){
            handlers.error(name);
        };

        var xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener("progress", uploadProgress, false);
        xhr.addEventListener("load", uploadComplete, false);
        xhr.addEventListener("error", uploadFailed, false);

        xhr.open("PUT", data['signed_request'], true);

        xhr.setRequestHeader('Content-Type', file.type);
        xhr.setRequestHeader('x-amz-acl', 'public-read');

        xhr.send(file);
    }

    $.ajax({
        type : 'GET',
        url : '/get-signature/',
        dataType : 'json',
        data : {
            s3_object_type : file.type,
            s3_object_name : file.name,
            csrfmiddlewaretoken: csrfTOKEN
        },
        success : uploadToS3
    });
}

window.uploadFile = uploadFile;

})();