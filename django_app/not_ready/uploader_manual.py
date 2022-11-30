"""
NOTE: WORK IN PROGESS

Helper methods to reprocess songs lost due to uploader not functioning
"""
import csv
import uploader

from media.models import *


def write_csv_f(fname, ids):
    csvf = open(fname, "w")
    csvw = csv.writer(csvf)
    csvw.writerows(ids)
    csvf.close()


def download_and_move_files_from_cloudfiles_to_s3():
    "process all songs still on cloudfiles to move all hosting to s3"
    pass


def songs_on_cloudfiles_but_not_processed(writecsv):
    """These can easily be set to processing = False, and online=True, will
    only be visible if visible=True.

    ** NOTE: Need to confirm before running this if I can set these to online
    since they are all offline

    """
    songs = [
        x.id
        for x in Song.objects.all()
        if x.streaming_url() and x.processing and not x.online
    ]

    if writecsv:
        write_csv_f("songs_on_cloudfiles_but_not_processed", songs)

    for song in Song.objects.filter(pk__in=songs):
        song.processing = False
        song.state = Song.SONG_STATE["READY"]
        song.online = True
        song.save()

    print("Affected records {}".format(len(songs)))


def songs_not_on_cloud_which_have_been_processed(writecsv):
    """These need to have processing set to FALSE and let the uploader
    see if it can find the files and reUpload them and set processed to true.
    This should be tested manually first. Not very hopefully of any file recovery
    but will report.
    """
    songs = [
        x.id for x in Song.objects.all() if not x.streaming_url() and not x.processing
    ]

    if writecsv:
        write_csv_f("songs_not_on_cloud_which_have_been_processed", songs)

    for song in Song.objects.filter(pk__in=songs):
        song.processing = True
        song.online = False
        song.state = Song.SONG_STATE["UPLOADED"]
        song.save()

    print("Affected records {}".format(len(songs)))


def songs_uploaded_to_s3(writecsv):
    "Find songs uploaded to s3 which are in the processing state and process them"
    songs = [x for x in Song.objects.all() if not x.streaming_url() and x.processing]
    songs_uploaded_to_s3 = [x for x in songs if x.was_uploaded_to_s3()]
    songs_uploaded_to_s3_ids = [x.id for x in songs_uploaded_to_s3]

    if writescv:
        write_csv_f("songs_uploaded_to_s3_ids.csv", songs_uploaded_to_s3_ids)

    for song in songs_uploaded_to_s3:
        uploader.process_song(song)
