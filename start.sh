#!/usr/local/bin/bash

cd /github/pegs
docker build -t baskoning/pegs .
docker run -ti -d -p 5000:5000 -e PORT=5000 baskoning/pegs
dockerid="$(docker ps -alq)"

rm -rf stop.sh
echo '#!/usr/local/bin/bash'>> stop.sh
echo >> stop.sh
echo 'echo copying files...' >> stop.sh
echo 'docker cp '$dockeridbash':/boards Files/' >> stop.sh
echo 'docker cp '$dockeridbash':/private/boardnames.txt Files/private/boardnames.txt' >> stop.sh
echo 'echo stopping server...' >> stop.sh
echo docker stop $dockerid >> stop.sh

echo 'To stop pegs: use bash stop.sh'