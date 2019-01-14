#!/usr/local/bin/bash

PORT=$1

re='^[0-9]+$'
if ! [[ $PORT =~ $re ]] ; then
   PORT=5000
fi

cd /github/pegscd 
docker build -t baskoning/pegs .
docker run -ti -d -p $PORT:$PORT -e PORT=$PORT baskoning/pegs
DOCKERID="$(docker ps -alq)"

rm -rf stop.sh
echo '#!/usr/local/bin/bash'>> stop.sh
echo >> stop.sh
echo 'echo copying files...' >> stop.sh
echo 'docker cp '$DOCKERID':/boards Files/' >> stop.sh
echo 'docker cp '$DOCKERID':/private/boardnames.txt Files/private/boardnames.txt' >> stop.sh
echo 'echo stopping server...' >> stop.sh
echo docker stop $DOCKERID >> stop.sh

echo 'using port '$PORT
echo 'To start pegs with a different port, for example 5001:'
echo 'bash start.sh 5001'
echo do
echo 'To stop pegs use:'
echo 'bash stop.sh'