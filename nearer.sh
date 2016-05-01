OLD="quit"

while true
do
	wget ftp://titanic.caltech.edu/nearer -O nearer
	NEW=`cat nearer`

	if [ "$OLD" != "$NEW" ]
	then
		OLD=$NEW
		killall mpv
		killall mpsyt
		eval mpsyt $NEW &
	fi

	sleep 10
done
