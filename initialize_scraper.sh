export GITHUBNAME=ReadySetOdds
export GITHUBPASSWORD=PASSWORD

apt-get install python3
apt-get install python3-pip
apt-get install xvfb xserver-xephyr vnc4server

git clone https://$GITHUBNAME:$GITHUBPASSWORD@github.com/ReadySetOdds/Thelinebacker.git
cd Thelinebacker
pip3 install -r requirements.txt
python3 set_database.py
Xvfb :99 -ac &
