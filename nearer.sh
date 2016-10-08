OLD="quit"

while true
do
	wget ftp://titanic.caltech.edu/nearer -O nearer
	NEW=`cat nearer`

	if [ "$OLD" != "$NEW" ]
	then
		OLD=$NEW
		killall -9 mpsyt
		sleep 1
		mpsyt $NEW &
	fi

	sleep 10
done
