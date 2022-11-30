#!/usr/bin/expect
# this is an expect script that takes in as an argument
#   an sftp bash command, sftpcommand
# it sftp's into the bank, provides a password, then
#   executes sftpcommand
# in this case, sftpcommand is "put ACH_FILENAME", which
#   will transfer the day's ach file to the bank's server.
# the script waits until the transfer is complete, then
# closes the sftp connection

spawn sftp hearusaach0424@ftpprd.svb.com
set sftpcommand [lindex $argv 0]
expect "assword:"
send "hearsvb0424\r"
expect "sftp>"
send "$sftpcommand\r"
expect "sftp>"
send "exit\r"
sleep 5
