// usage: node jslint.node.js files.js ...
var util,fs,path,$,jslint;
util   = require('util');
fs    = require('fs');
path  = require('path');
//$     = require('jquery');
eval( require('fs').readFileSync('./lint/jslint.js','utf8') ); // pseudo require file
jslint = JSLINT;

var argv = process.argv.splice(2);

exempt = [ 'Don\'t make functions within a loop.', 
	   'Unexpected \'else\' after \'return\'.', 
	   'The body of a for in should be wrapped in an if statement to filter unwanted properties from the prototype.',
	   'Unexpected dangling \'_\' in'
	 ];

function validate(filename, callback) {
    fs.readFile(filename, 'utf8', function(err, file) {
	var predef;
	util.print('checking ' + filename.substring(filename.lastIndexOf('/')+1,filename.length) + '...');
	predef = [ '$','History' ];
	jslint.jslint( file.replace(/^\#\!.*/, ''),

		       { maxerr: 10,
			 indent: 4, 
			 css: true,
			 predef: predef,
			 sloppy: true,
			 white: true,
			 browser: true
		       }
		       
		     );
        callback( remExempt( jslint.data().errors ) );//$.extend( true, {}, {}, jslint.errors ) );
    });
}

function contains(array, element) {
    for (var i = 0; i < array.length; i++) {
	if (element.indexOf(array[i]) > -1) { // something in array is a substring of element
	    return true;
	}
    }
    return false;
}

function remExempt(errors) {
    var err;

    for (err in errors) {
	if ( errors[err] !== null && contains(exempt, errors[err].reason) ) {
	    delete errors[err];
	}
    }
    
    return errors;    
}

function main() {
    for (i in argv) {
	var filename;
	filename = argv[i];
	validate( filename, function(errors){
	    var err;
	    
	    errors = remExempt(errors);

//	    if ($.isEmptyObject( errors )) {
	    if ( errors === undefined || errors["0"] === undefined ) { //lol
		// no errors
		console.log( '\t', 'OK' );
	    } else {
		console.log( '\t', 'BAD' );
		console.log( '' );
		for (i in errors) {
		    err = errors[i];
		    if (err === null) {
			//too many errors
		    } else {
			console.log( '', 'where:', 'line', err.line, 'char', err.character );
			console.log( '', 'what: ', err.evidence );
			console.log( '', 'why:  ', err.reason );
			console.log( '' );
		    }
		}
		process.exit(1);
	    }
	});
    }
}

main();
    
/*
function walk(filename, callback){
    fs.stat(filename, function(err, stats) {
        if(stats.isFile() && filename.match(/\.js$/)) {
            // Filename - do callback
            callback(filename);
        } else if(stats.isDirectory()) {
            // Directory - walk recursive
            fs.readdir(filename, function(err, files) {
                for(var i = 0; i < files.length; i++) {
                    walk(filename + '/' + files[i], callback);
                }
            });
        }
    });
}

walk(__dirname, function(filename) {
    // Check each file at the beginning
    validate(filename, status);

    // Watch every JS file for changes
    fs.watchFile(filename, function(curr, prev) {
        if(curr !== prev) {
            validate(filename, status_and_growl);
        }
    });
});
*/
