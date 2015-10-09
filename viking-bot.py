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
                    # add to the config object
                    self.config[line.group(1)] = line.group(2)
        # if no config found then exit
        else:
            print("Config file wasn't found (./../viking.conf)")
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
                # get useful data from it and pass it on
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
            print("PRIVMSG " + channel + ": " + message)
        else:
            self.s.send(bytes("%s %s :%s\r\n" % (type, channel, message), "UTF-8"))
            print(type + " " + channel + ": " + message)

    def auth(self):
        self.send("", "NickServ", "identify " + self.password)


# commands
commands = []

# command class
class command:

    def __init__(self, name, helptxt):
        self.name = name
        self.helptxt = helptxt

        commands.append(self)

    def execute(self, string, channel):
        cmd = self.name

        if(cmd == "-g"):
            search_google(string, channel, "web")
        elif(cmd == "-gi"):
            search_google(string, channel, "images")
        elif(cmd == "-imdb"):
            search_imdb(string, channel)
        elif(cmd == "-wp"):
            search_wp(string, channel)

# was command written?
def parse_msg(unparsed_msg):

    # make stuff more readable
    sender  =   unparsed_msg.group(1) # sender of message 
    ident   =   unparsed_msg.group(2) # used to verify nickname if registered to nickserv
    type    =   unparsed_msg.group(3) # we already know this is PRIVMSG
    channel =   unparsed_msg.group(4) # where message was written, can also be a nickname
    message =   unparsed_msg.group(5).replace("\r\n", "").replace("\r", "").replace("\n", "") # message string

    # if owner sends commands through private message
    if(ident == vbot.owner and channel == vbot.nick):
        if("join" in message):
            chan = message.split("#")
            bot_do("join", chan[1])
        elif("part" in message):
            chan = message.split("#")
            bot_do("part", chan[1])
        elif("quit" in message):
            bot_do("quit", "")

    # if message seems to be a command
    if(message.startswith("-") and not message.startswith("-help")):
        try:
            cmz = re.search("(-\w+)\s+(.+)", message)
            cmd = cmz.group(1)
            string = cmz.group(2)
        except (AttributeError):
            vbot.send("", channel, "Bad input, see -help if retarded")
            return
        for command in commands:
            if(command.name == cmd):
                command.execute(string, channel)
    # if mentioned or -help
    elif(vbot.nick in message or message.startswith("-help")):
        bot_help(sender)

# bot functions
def bot_help(sender):
    vbot.send("", sender, "In case you didn't know, I'm a bot, shocker. I can do the following:")

    for cmd in commands:
        vbot.send("", sender, cmd.helptxt)

def bot_do(what, chan):
    if(what == "join"):
        vbot.send("JOIN", "#"+chan, "")
    elif(what == "part"):
        vbot.send("PART", "#"+chan, "")
    elif(what == "quit"):
        sys.exit()

# replace this with ddg in secret
# https://developers.google.com/image-search/v1/jsondevguide?hl=en
def search_google(search_string, chan, stype):
    query = urllib.parse.urlencode({'q': search_string})
    url = 'https://ajax.googleapis.com/ajax/services/search/%s?v=1.0&%s' % (stype, query)
    search_response = urllib.request.urlopen(url)
    search_results = search_response.read().decode("utf8")
    results = json.loads(search_results)
    try:
        data = results['responseData']['results'][0]['unescapedUrl']
        vbot.send("", chan, data)
    except Exception as e:
        vbot.send("", chan, "Jag fann inget")
        error("search_google", e)
        return


# http://www.omdbapi.com/
def search_imdb(search_string, chan):

    if("+" in search_string):
        year = search_string.split("+")[1]
        search_string = search_string.split(" +")[0]
        query = urllib.parse.urlencode({'t': search_string})
        query2 = urllib.parse.urlencode({'y': year})
        url = 'https://www.omdbapi.com/?%s&%s&tomatoes=true&plot=short&r=json' % (query, query2)
    else:
        query = urllib.parse.urlencode({'t': search_string})
        url = 'https://www.omdbapi.com/?%s&tomatoes=true&plot=short&r=json' % query

    search_response = urllib.request.urlopen(url)
    search_results = search_response.read().decode("utf8")
    results = json.loads(search_results)

    try:
        data = results
        string1 = data['Title'] + " (" + data['Year'] + ") (" + data['Genre'] + ")"
        string2 = "[IMDB] " + data['imdbRating'] + "/10 [RT] " + data['tomatoMeter'] + "% - " + data['tomatoUserMeter'] + "% [META] " + data['Metascore'] + "/100 - " + data['Website']
        vbot.send("", chan, string1)
        vbot.send("", chan, string2)
    except Exception as e:
        vbot.send("", chan, "Jag fann inget")
        error("search_imdb", e)
        return

def search_wp(search_string, chan):
    query = urllib.parse.urlencode({'titles': search_string})
    url = 'https://en.wikipedia.org/w/api.php?format=json&formatversion=2&action=query&prop=extracts&exintro=&explaintext=&redirects&%s' % query
    search_response = urllib.request.urlopen(url)
    search_results = search_response.read().decode("utf8")
    results = json.loads(search_results)
    try:
        title = results['query']['pages'][0]['title']
        summary = results['query']['pages'][0]['extract'][:100] + "..."
        data = title + " [https://en.wikipedia.org/wiki/" + title +"]"
        vbot.send("", chan, data)
        vbot.send("", chan, summary)
    except Exception as e:
        vbot.send("", chan, "Jag fann inge")
        error("search_wp", e)
        return

def error(place, e):
    print('\033[1;41m[%s] Caught exception: %s\033[1;m' % (place,e))

# commands
# search engines
google      =   command("-g",
                    "-g         <string>                    - Search google")
google_i    =   command("-gi",
                    "-gi        <string>                    - Search google images")
imdb        =   command("-imdb",
                    "-imdb      <name +year(optional)>      - Search imdb")
wp          =   command("-wp",
                    "-wp        <string>                    - Search wikipedia")

#
# misc
poem        =   command("-poem",
                    "-poem                                  - Links the poem of the day")
quote       =   command("-quote",
                    "-quote     <string(optional)>          - Search for quote, leave blank for QoTD or write 'random'")

#
# bot related
bhelp       =   command("-help",
                    "-help      <command(optional)>         - Display commands or help for a command")

# start it all
vbot = bot()
vbot.connect()
vbot.loop()
