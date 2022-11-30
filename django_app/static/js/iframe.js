/**
 *  iframe.js
 *  
 *  handles iframe javascript, like file upload interface scripting
 */

$(document).ready( function() {
	
	$("#songUploadForm").submit(function(e) {
		
		/* For this little hack, see http://airbladesoftware.com/notes/note-to-self-prevent-uploads-hanging-in-safari */
		if (/AppleWebKit|MSIE/.test(navigator.userAgent)) {
			$.ajax( "/close-connection",
					{async: false});
		}
		
		
		
		$("#submitSong").attr('disabled', true);
		$("#submitSong").val('Uploading...');
		
	});
	
$("photoUploadForm").submit(function(e) {
		
		/* For this little hack, see http://airbladesoftware.com/notes/note-to-self-prevent-uploads-hanging-in-safari */
		if (/AppleWebKit|MSIE/.test(navigator.userAgent)) {
			$.ajax( "/close-connection",
					{async: false});
		}
		
		
		
		$("#submitPhoto").attr('disabled', true);
		$("#submitPhoto").val('Uploading...');
		
	});
	
});
