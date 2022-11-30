/* vars.js
first file
*/

(function(){
var requestId, currentRequestId, sessionInfo, DOWNLOAD_FORMATS, LOGGED_IN;

LOGGED_IN = false;

requestId = 1;

currentRequestId = 1;

// needs to be updated if media.constants is changed
DOWNLOAD_FORMATS = ['mp3 320','mp3 V0','mp3 V2','FLAC'];  //'m4a',

sessionInfo = {
    cur_account: null,
    accounts: null
};

window.requestId = requestId;
window.currentRequestId = currentRequestId;
window.sessionInfo = sessionInfo;
window.DOWNLOAD_FORMATS = DOWNLOAD_FORMATS;
window.LOGGED_IN = LOGGED_IN;

})();
