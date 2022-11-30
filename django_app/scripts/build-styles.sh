#! /bin/bash

current=${PWD##*/}

if [ $current = "scripts" ]
then
  cd ..
fi


# Remove the old compiled file so we don't re-include it with the wildcard call below
rm static/css/compiled.css

lessc static/css/*.less >> static/css/comp2

cat static/fonts/font-face.css static/css/*.css > static/css/comp1

cat static/css/comp2 > static/css/comp1
rm static/css/comp2

mv static/css/comp1 static/css/compiled.css

cleancss -o static/css/compiled.min.css static/css/compiled.css
