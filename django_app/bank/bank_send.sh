#!/bin/bash/

# this script creates an ach file by calling 'python create_ach.py'
# create_ach prints its filename, which is grabbed in bash and saved
#   as variable ACH_FILENAME
# "put ACH_FILENAME" is passed as an argument to the expect program
#   bank_expect.sh
ACH_FILENAME="$(python manage.py pay_artists)"
expect bank/bank_expect.sh "put $ACH_FILENAME"
echo "ACH file transferred to the bank."
