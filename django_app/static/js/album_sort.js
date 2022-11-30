/* album_sort.js

*/



//import
//are these 3 supposed to be a global imports?
/*global
albums : true, 
tracks : true,
album_tracks : true, 
copyAllTracks,
refreshContent,
updateAlbumTracks,
confirm,
saveContent,

*/

(function(){
    
    function Song(songid, title, length) {
	this.songid = songid;
	this.title = title;
	this.length = length;
    }
    
    function Album(albumid, title) {
	this.albumid = albumid;
	this.title = title;
    }
    
    function albumSortInit() {
	var 
	albums = [];
	albums.push(new Album(-2, 'Singles/uncategorized'));
	tracks = [];
	album_tracks = [];
	album_tracks[0] = [];
    }
    
    function addSongToAlbum(songid,title,length,albumid) {
	var i;
	tracks.push(new Song(songid,title,length));
	if(albumid==='' || albumid==='-2') {
	    album_tracks[0].push(tracks.length-1);
	    return;
	}
	for(i=0; i<album_tracks.length; i=i+1) {
	    if(albums[i].albumid===albumid) {
		album_tracks[i].push(tracks.length-1);
	    }
	}
    }
    
    function updateSortable() {
	$(function() {
	    $( ".album_tracks_list" ).sortable({
		connectWith: ".album_tracks_list", 
		tolerance: 'pointer', 
		scroll: false,
		containment: '#albumSelect'
	    }).disableSelection();
	});
    }
    
    function addAlbum(albumid, title) {
	var num;
	num = albums.length;
	albums[num] = new Album(albumid, title);
	album_tracks[num] = []; 
    }
    
    function removeAlbum(num) {
	if(num===0) { return; } // Don't allow removal of "Singles/uncategorized"
	copyAllTracks(num,0); 
	album_tracks.splice(num,1);
	albums.splice(num,1);
	refreshContent();
    }
    
    function removeAlbumCmd(num) {
	if(confirm("Remove album \""+albums[num].title+"\"?")) {
	    removeAlbum(num);
	}
    }
    
    function copyAllTracks(from, to) {
	var i;
	updateAlbumTracks();
	for(i=0; i<album_tracks[from].length; i=i+1) {
	    album_tracks[to].push(album_tracks[from][i]);
	}
    }
    
    function addAlbumCmd() {
	var addAlbumField, newName;
	addAlbumField= document.getElementById('addAlbumField');
	newName = addAlbumField.value;
	if(addAlbumField.value==='') { return; }
	addAlbum(-1,newName);
	addAlbumField.value = '';
	addAlbumField.focus();
	updateAlbumTracks(); // save current track orders
	refreshContent();
    }
    
    function refreshContent() {
	var content_fill, content, i, albumTitleStr, j, track_num, songid;
	content_fill = document.getElementById('content_fill');
	content = "<table id='albumSelect' style='width:300px; align:left'><tr>";
	for(i=0; i<albums.length; i=i+1) {
	    if(i%3===0 && i!==0) {
		content += "</tr><tr>";
	    }
	    if(i!==0) {
		albumTitleStr = "<span class='album_edit' onClick='editAlbum("+i+")'>"+albums[i].title+"</span>";
	    } else {
		albumTitleStr = albums[i].title;
	    }
	    content += "<td class='album_tracks_td'>"+albumTitleStr;
	    if(i!==0) {
		content += " <span class='album_delete' onClick='removeAlbumCmd("+i+");' title='Delete album'>[x]</span>";
	    }
	    content += "<p><ul id='album"+i+"'; class='album_tracks_list'>";
	    for(j=0; j<album_tracks[i].length; j=j+1) {
		track_num = album_tracks[i][j];
		songid = tracks[track_num].songid;
		content += "<li id='track"+track_num+"' class='track'>"+tracks[track_num].title+
		    " <span style='font-size:xx-small'>["+tracks[track_num].length+"]</span></li>";
	    }
	    content += "</ul></td>";
	}
	content += "</tr></table>";
	content_fill.innerHTML = content;
	updateSortable();
    }
    
    /* Updates album_tracks according to current track order in browser */
    function updateAlbumTracks() {
	var i;
	for(i=0; i<albums.length; i=i+1) {
	    album_tracks[i] = $('#album'+i).sortable('toArray').map(function(item) {
		return item.split('track')[1];
	    });
	}
    }
    
    
    /* Returns an object representing the current state of album_tracks (as strings) */
    function outputAlbumData() {
	var album_data, i, album_list, j;
	album_data = [];
	for(i=0; i<album_tracks.length; i=i+1) {
	    album_list = [];
	    album_list.push(albums[i]);
	    for(j=0; j<album_tracks[i].length; j=j+1) {
		album_list.push(tracks[album_tracks[i][j]]);
	    }
	    album_data[i] = album_list;
	}
	return album_data;
    }
    
    $("#saveButton").click(function(e) {
	saveContent(true);
    });
    
    /* @param boolean show_result - if true, refresh content and show success or failure message 
     */
    function saveContent(show_result) {
	var album_data;
	updateAlbumTracks();
	album_data = {albumData: outputAlbumData()};
	$.post('/my-account/albums?ajax=true', album_data, 
	       function(data) { 
		   if(show_result) {
		       $("#content").html( data.content );
		   }
	       },
	       'json');
    }
    
    function editAlbum(num) {
	var albumid;
	albumid = albums[num].albumid;
	if(albumid < 0) {
	    // TODO: fix this
	    alert("Please save before making changes to this new album.");
	    return;
	}
	saveContent(false);
	window.location = "/my-account/albums/edit?albumid="+albumid;
    }
    
    $(document).ready(function() {
	var addAlbumField = $("#addAlbumField");
	$(addAlbumField).focus(function(e) {
	    if (this.defaultValue===this.value) {
		this.value = '';
	    }
	});
	$(addAlbumField).blur(function(e) {
	    if (this.value==='') {
		this.value = this.defaultValue;
	    }
	});
	$(addAlbumField).keydown(function(e) {
	    if (e.keyCode===13) {
		addAlbumCmd();
	    }
	});
	$("#addAlbumButton").mouseover(function(e) {
	    this.style.cursor='pointer';
	});
	$("#addAlbumButton").mouseout(function(e) {
	    this.style.cursor='auto';
	});
	$("#addAlbumButton").click(function(e) {
	    addAlbumField = document.getElementById('addAlbumField');
	    if (addAlbumField.value!==addAlbumField.defaultValue) {
		addAlbumCmd();
	    }
	    else {
		addAlbumField.focus();
	    }
	});
    });
    
}());
