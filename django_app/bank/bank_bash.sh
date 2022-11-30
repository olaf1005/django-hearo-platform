#!/bin/bash/

# this script creates an ach file by calling 'python create_ach.py'
# create_ach prints its filename, which is grabbed in bash and saved
#   as variable ACH_FILENAME
# "put ACH_FILENAME" is passed as an argument to the expect program
#   sftp_send.sh

ACH_FILENAME="$(python manage.py pay_artists)"

if [ "$ACH_FILENAME" == "NONE" ]
then
  exit 0
else
  ACH_TRANSMITTAL_FILENAME="$(python manage.py create_transmittal_record)"
  expect /root/hearo/bank/sftp_send.sh "$ACH_TRANSMITTAL_FILENAME"
  expect /root/hearo/bank/sftp_send.sh "$ACH_FILENAME"
  echo "======================= $ACH_TRANSMITTAL_FILENAME and $ACH_FILENAME successfully wired to Silicon Valley" >> /home/ry/logs/payments.log
fi
