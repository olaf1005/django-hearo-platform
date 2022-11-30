(function() {

  window.S3Upload = (function() {
    S3Upload.prototype.s3_sign_put_url = '/signS3put';

    S3Upload.prototype.file = null;
    S3Upload.prototype.albumid = null;

    S3Upload.prototype.onFinishS3Put = function(public_url, data) {
      return console.log('base.onFinishS3Put()', public_url);
    };

    S3Upload.prototype.onProgress = function(percent, status) {
      return console.log('base.onProgress()', percent, status);
    };

    S3Upload.prototype.onError = function(status) {
      return console.log('base.onError()', status);
    };

    function S3Upload(options) {
      if (options == null) options = {};
      _.extend(this, options);
      this.onProgress(0,'Upload started');
      return this.uploadFile(this.file);
    }

    S3Upload.prototype.createCORSRequest = function(method, url) {
      var xhr;
      xhr = new XMLHttpRequest();
      if (xhr.withCredentials != null) {
        xhr.open(method, url, true);
      } else if (typeof XDomainRequest !== "undefined") {
        xhr = new XDomainRequest();
        xhr.open(method, url);
      } else {
        xhr = null;
      }
      return xhr;
    };

    S3Upload.prototype.executeOnSignedUrl = function(file, callback) {
      var this_s3upload, xhr;
      var ai = this.albumid;
      this_s3upload = this;
      xhr = new XMLHttpRequest();
      if (file.type == ''){
        var ftype = file.name.split('.');
        ftype = ftype[ftype.length - 1];
        if (ftype == 'flac'){
	  xhr.open('GET', this.s3_sign_put_url + '?albumid='+ai+'&s3_object_type=audio/flac&s3_object_name=' + file.name, true);
        }
      } else {
	xhr.open('GET', this.s3_sign_put_url + '?albumid='+ai+'&s3_object_type=' + file.type + '&s3_object_name=' + file.name, true);
      }

      xhr.overrideMimeType('text/plain; charset=x-user-defined');
      xhr.onreadystatechange = function(e) {
        var result;
        if (this.readyState === 4 && this.status === 200) {
          try {
            result = JSON.parse(this.responseText);
          } catch (error) {
            this_s3upload.onError('bad_json');
            return false;
          }
          console.log("FINISHED SIGNING")
          console.log(result);
          return callback(decodeURIComponent(result.signed_request), result.url, result.data);
        } else if (this.readyState === 4 && this.status !== 200) {
          return this_s3upload.onError(this.status);
        }
      };
      return xhr.send();
    };

    S3Upload.prototype.uploadToS3 = function(file, url, public_url, data) {
      var this_s3upload, xhr;
      this_s3upload = this;
      xhr = this.createCORSRequest('PUT', url);
      if (!xhr) {
        this.onError('not_supported');
      } else {
        xhr.onload = function() {
          if (xhr.status === 200) {
            this_s3upload.onProgress(100, 'Upload completed.');
            return this_s3upload.onFinishS3Put(public_url, data);
          } else {
            return this_s3upload.onError(xhr.status);
          }
        };
        xhr.onerror = function(e) {
          console.log(e);
          return this_s3upload.onError('xhr', data);
        };
        xhr.upload.onprogress = function(e) {
          var percentLoaded;
          if (e.lengthComputable) {
            percentLoaded = Math.round((e.loaded / e.total) * 100);
            return this_s3upload.onProgress(percentLoaded, percentLoaded === 100 ? 'Finalizing.' : 'Uploading.');
          }
        };
      }
      if (file.type == ''){
        var ftype = file.name.split('.');
        ftype = ftype[ftype.length - 1];
        if (ftype == 'flac'){
          xhr.setRequestHeader('Content-Type', 'audio/flac');
        }
      } else {
        xhr.setRequestHeader('Content-Type', file.type);
      }
      xhr.setRequestHeader('x-amz-acl', 'public-read');
      return xhr.send(file);
    };

    S3Upload.prototype.uploadFile = function(file) {
      var this_s3upload;
      this_s3upload = this;
      return this.executeOnSignedUrl(file, function(signedURL, publicURL, data) {
        return this_s3upload.uploadToS3(file, signedURL, publicURL, data);
      });
    };

    return S3Upload;

  })();

}).call(this);
