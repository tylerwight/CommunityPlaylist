#!/bin/bash
#Tyler WIght
# setup environment to run discord mysql bot
sudo apt install python3
sudo apt install python3-pip
pip install discord
pip install python-dotenv
pip install mysql-connector-python
pip install spotipy
pip install flask
sudo apt install mysql-server
sudo systemctl start mysql.service

#this part is to fix a bug where running mysql_secure_installation fails on ubuntu server as of July2022. 
# it fails with "... Failed! Error: SET PASSWORD has no significance for user 'root'@'localhost' as the authentication method used doesn't store authentication data in the MySQL server. Please consider using ALTER USER instead if you want to change authentication parameters." in a loop and you can't get out
# we are going to change some settings to allow  mysql_secure_installation to work

sudo mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';"

echo "the password for mysql_secure_install is 'password'. This will change when you are done"

sudo mysql_secure_installation

echo "It's gonna ask for the password you just typed to revert the change we made to allow mysql_secure_install to circumvent the bug"

mysql -u root -p  -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH auth_socket;"

sudo mysql -u root -e "CREATE USER 'discord'@'localhost' IDENTIFIED BY 'password';"

sudo mysql -u root -e "CREATE DATABASE discord; use discord; CREATE TABLE guilds (guild_id varchar(255), name varchar(255), spotipy_username varchar(255), watch_channel varchar(255), enabled BOOL, playlist_name varchar(255), playlist_id varchar(255));"

sudo mysql -u root -e "GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on *.* TO 'discord'@'localhost';"

echo "the user discord has been created with the password 'password', please change this"



