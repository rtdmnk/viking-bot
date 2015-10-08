#!/usr/bin/env python3

import sys
import socket
import string
import re
import urllib.parse
import urllib.request
import json
import os.path

class bot:

    def __init__(self):

        self.config = {}

        # if config file exists, parse it
        if(os.path.isfile("./../viking.conf")):
            lines = [line.rstrip('\n') for line in open('./../viking.conf')]

            for line in lines:
                # if comment or empty: pass
                if(line.startswith("#") or line == ""):
                    pass
                else:
                    # remove uneeded things
                    line = line.replace(" ", "").replace("\t", "").replace("'", "").replace('"', "")
                    # get the values
                    line = re.match('(\w+)=(.+)', line)
                    # add to the object
                    self.config[line.group(1)] = line.group(2)
        # if no config found then exit
        else:
            print("Config file wasn't found (./viking.conf)")
            sys.exit()

        self.host = self.config['host']
        self.port = int(self.config['port'])

        self.nick = self.config['nick']
        self.ident = self.config['ident']
        self.realname = self.config['realname']

        self.owner = self.config['owner']

        if(self.config['nickserv']):
            self.password = self.config['password']

    # Connect and set user information
    def connect(self):
        self.s = socket.socket( )
        self.s.connect((self.host, self.port))

        self.s.send(bytes("NICK %s\r\n" % self.nick, "UTF-8"))
        self.s.send(bytes("USER %s %s elknet :%s\r\n" % (self.ident, self.host, self.realname), "UTF-8"))

    def loop(self):
        # read shit
        readbuffer = ""

        while 1:
            readbuffer = readbuffer+self.s.recv(1024).decode("UTF-8")
            temp = str.split(readbuffer, "\n")
            readbuffer=temp.pop( )

            # print recieved messages
            print(temp[0])

            # if message recieved
            if(temp[0].find("PRIVMSG") > 0):
                # get useful data from it and send it on
                # 1:nick, 2:ident, 3:type, 4:?, 5:message
                message = re.search(':(.+)!.+@(.+) (\w+) (.+) :(.+)', temp[0])
                parse_msg(message)
            # if nickserv complains and should complain
            elif("NickServ" in temp[0] and "registered" in temp[0] and self.password):
                self.auth()
            # if ping
            elif("PING" in temp[0]):
                self.send("PONG", "", temp[0])

    # make sending messages easier
    def send(self, type, channel, message):
        if(type == ""):
            self.s.send(bytes("PRIVMSG %s :%s\r\n" % (channel, message), "UTF-8"))
        else:
            self.s.send(bytes("%s %s :%s\r\n" % (type, channel, message), "UTF-8"))

        print(type + " " + channel + ": " + message)

    def auth(self):
        self.send("", "NickServ", "identify " + self.password)

vbot = bot()
vbot.connect()
vbot.loop()

sys.exit()
# commands
commands = []

# command class
class command:

    def __init__(self, cmd, helptxt, execute):
        self.cmd = cmd
        self.helptxt = helptxt
        self.execute = execute

        commands.append(self)

# was command written?
def parse_msg(message):

    command = message.group(5).replace("\r\n","")

    print(command)

    # creator commands in privmessage
    if(message.group(2) == creator and message.group(4) == NICK):

        if("join" in command):
            chan = command.split("#")
            join_chan(chan[1])
            print("joining #" + chan[1])
        elif("part" in command):
            chan = command.split("#")
            part_chan(chan[1])
        elif(command == "quit"):
            bot_quit()

    # command wherever
    if(command.startswith("-")):

        cmd = command.split('-')
        cmd = cmd[1].split(' ')
        cmd = cmd[0]

        if(cmd == "g"):
            string = command.split('-g ')
            search_google(string[1], message.group(4), "web")
        elif(cmd == "gi"):
            string = command.split('-gi ')
            search_google(string[1], message.group(4), "images")
        elif(cmd == "imdb"):
            string = command.split('-imdb ')
            search_imdb(string[1], message.group(4))

    # if mentioned or -help
    if(NICK in command or command.startswith("-help")):
        bot_help(message.group(1))

# bot functions
def send(who, msg):
    print(who + ": " + msg)
    s.send(bytes("PRIVMSG %s :%s\r\n" % (who, msg), "UTF-8"))

def authenticate():
    send("NickServ", "identify " + password)

def bot_help(sender):
    send(sender, "In case you didn't know, I'm a bot, shocker. I can do the following:")

    for cmd in commands:
        send(sender, cmd.helptxt)


# replace this with ddg in secret
# https://developers.google.com/image-search/v1/jsondevguide?hl=en
def search_google(search_string, chan, stype):
    query = urllib.parse.urlencode({'q': search_string})
    url = 'http://ajax.googleapis.com/ajax/services/search/%s?v=1.0&%s' % (stype, query)
    search_response = urllib.request.urlopen(url)
    search_results = search_response.read().decode("utf8")
    results = json.loads(search_results)

    try:
        data = results['responseData']['results'][0]['unescapedUrl']
    except (ValueError,IndexError):
        data = "Jag fann inget"
        print("caught exception")

    send(chan, data)


# http://www.omdbapi.com/
def search_imdb(search_string, chan):

    if("+" in search_string):
        year = search_string.split("+")[1]
        search_string = search_string.split(" +")[0]
        query = urllib.parse.urlencode({'t': search_string})
        query2 = urllib.parse.urlencode({'y': year})
        url = 'http://www.omdbapi.com/?%s&%s&tomatoes=true&plot=short&r=json' % (query, query2)
    else:
        query = urllib.parse.urlencode({'t': search_string})
        url = 'http://www.omdbapi.com/?%s&tomatoes=true&plot=short&r=json' % query

    search_response = urllib.request.urlopen(url)
    search_results = search_response.read().decode("utf8")
    results = json.loads(search_results)

    try:
        data = results
        string1 = data['Title'] + " (" + data['Year'] + ") (" + data['Genre'] + ")"
        string2 = "[IMDB] " + data['imdbRating'] + "/10 [RT] " + data['tomatoMeter'] + "% - " + data['tomatoUserMeter'] + "% [META] " + data['Metascore'] + "/100 - " + data['Website']
    except (ValueError,IndexError,KeyError):
        data = "Jag fann inget"

    send(chan, string1)
    send(chan, string2)


def join_chan(chan):
    s.send(bytes("JOIN #%s\r\n" % chan, "UTF-8"))
    print("joined " + chan)

def part_chan(chan):
    s.send(bytes("PART #%s\r\n" % chan, "UTF-8"))
    print("left " + chan)

def priv_msg(nick, msg):
    s.send(bytes("PRIVMSG %s :%s\r\n" % (nick, msg), "UTF-8"))

def bot_complain(chan):
    s.send(bytes("PRIVMSG %s :nah, fuck you\r\n" % chan, "UTF-8"))

def bot_quit():
    sys.exit()

# commands
google  =   command("-g", "-g <string> - Search google", "search_google(string, channel, g)")
google_i=   command("-gi", "-gi <string> - Search google images", "google(string, channe, gi)")
imdb    =   command("-imdb", "-imdb <name +year(optional)> - Search imdb", "search_imdb(string, channel)")
bhelp   =   command("-help", "-help <command(optional)> - Display commands or help for a command", "bot_help(string, channel)")
