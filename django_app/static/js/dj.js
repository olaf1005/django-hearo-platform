/* dj.js

*/

//import
/*global
io,
player,
loadUserRadio,
soundManager,
console,
*/

(function(){

    function sendDjMessage(asocket){
	var sm, id, playing, offset, vol;
	sm = soundManager.getSoundById("playing");
        vol = player.volume;
        id = player.songQueue[0].songid;
        playing = '0';
        if(player.isPlaying){playing = '1';}
        offset = Math.floor(sm.position/1000);
	asocket.send(
	    {action:"djmessage", message: id+' '+offset+' '+playing+' '+vol});
    }

    function startSession(uid){
	$.post("/on-air/start-session/",{uid_session:uid},function(data){
	    var parsed, socket;
	    parsed = data;
	    socket = new io.Socket();
	    socket.connect();
	    socket.on('connect',function(){
		socket.subscribe(parsed.room_name);
		socket.send({action:'started'});
	    });
	    socket.on('message',function(data){
		var songid;
		if(data.action === 'joined'){
                    sendDjMessage(socket);
		}
	    });
	});
    }


    function joinSession(){
        //console.log('clicked');
	var uid;
	uid = $("#current_uid").val();
	$.get("/on-air/status/"+uid,function(data){
	    var par;
	    par = data;
            //console.log(uid);
            //console.log(par.id);
            if(par.id === parseInt(uid,10)){
                //console.log('start');
                startSession(uid);
	    }else if(par.canConnect){
		$.post("/on-air/join-session/",{uid_session:uid},function(data){
		    var socket, parsed;
		    socket = new io.Socket();
		    parsed = data;
		    socket.connect();
		    socket.on('connect',function(){
			// use data to determine room name
			socket.subscribe(parsed.room_name);
		    });
		    socket.on('message',function(data){
			var args, songid, offset, playing, volume;
			if(data.action === 'djmessage'){
			    args = data.message.split(" ");
			    songid = parseInt(args[0], 10);
			    offset = parseInt(args[1], 10);
			    playing = parseInt(args[2], 10);
			    volume = parseInt(args[3], 10);
			    if(player){
				player.clearPlayQueue();
				player.addSong(songid);
				if(playing === 0){
				    setTimeout(function(){player.setPosition(offset);},2000);
				    player.pause();
				}else{
				    setTimeout(function(){
					player.setPosition(offset+2);
					player.resume();
				    },2000);
				}
				// use volume arg
                                player.setVolume(volume);
			    }
			}
		    });
		});
	    }else{
		player.initRadio(uid);
	    }
	});
    }

    //export
    window.startSession = startSession;
    window.joinSession = joinSession;

}());
