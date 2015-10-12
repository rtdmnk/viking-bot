#!/usr/bin/env python3
import sys, getopt, re, time, os.path, string, json, traceback
import socket, ssl
import urllib.parse, urllib.request
from bs4 import BeautifulSoup
from urllib.request import urlopen

# globals
config_file = ""
verbose = False
commands = []

class bot:

    def __init__(self):
        self.config = {}
        global config_file

        # Dummy values
        self.host = "chat.freenode.com"
        self.port = 6667
        self.ssl = False

        self.nick = "VikingIRCBot"
        self.ident = "info"
        self.realname = "Amanita Muscaria"

        self.owner = "Oden"
        self.log = ""

        self.nickserv = False


        # if config file exists, parse it
        if(config_file):
            pass
        else:
            config_file = "./vikingBot.conf"
        if(os.path.isfile(config_file)):
            lines = [line.rstrip('\n') for line in open(config_file)]

            for line in lines:
                # if comment or empty: pass
                if(line.startswith("#") or line == ""):
                    pass
                else:
                    # parse, get values and add it to the config object
                    line = line.replace(" ", "").replace("\t", "").replace("'", "").replace('"', "")
                    line = re.match('(\w+)=(.+)', line)
                    self.config[line.group(1)] = line.group(2)

            # Put config to corresponding variables
            self.host = self.config['host']


            self.port = int(self.config['port'])

            self.nick = self.config['nick']
            self.ident = self.config['ident']
            self.realname = self.config['realname']

            self.owner = self.config['owner']

            self.log = self.config['log_file']

            self.nickserv = self.config['nickserv']

            if("+" in self.config['port']):
                self.ssl = True

            if(self.nickserv):
                self.password = self.config['password']
        # if no config found then exit
        else:
            print("Config file wasn't found (" + config_file + ")")
            string = input("Use dummy settings? [y/n]")
            if(string.lower() == "y"):
                pass
            else:
                print("quitting")
                sys.exit()

        self.commands()

    def commands(self):
        # search engines
        #
        google      = command("-g",
                "-g         <string>                    - Search google")
        google_i    = command("-gi",
                "-gi        <string>                    - Search google images")
        imdb        = command("-imdb",
                "-imdb      <name +year(optional)>      - Search imdb")
        wp          = command("-wp",
                "-wp        <string>                    - Search wikipedia")

        #
        # misc
        #
        poem        = command("-poem",
                "-poem                                  - Links the poem of the day")
        quote       = command("-quote",
                "-quote                                 - Fetch random quote from forismatic.com")

        #
        # bot related
        #
        bhelp       = command("-help",
                "-help      <command(optional)>         - Display commands or help for a command")

    # Connect and set user information
    def connect(self):
        if(self.ssl):
            simply_s = socket.socket()
            self.s = ssl.wrap_socket(simply_s)
        else:
            self.s = socket.socket()

        self.s.connect((self.host, self.port))

        self.s.send(bytes("NICK %s\r\n" % self.nick, "UTF-8"))
        self.s.send(bytes("USER %s %s elknet :%s\r\n" % (self.ident, self.host, self.realname), "UTF-8"))

    # main loop
    def loop(self):
        readbuffer = ""
        while 1:
            # fetch message, parse it
            readbuffer = readbuffer+self.s.recv(1024).decode("UTF-8")
            temp = str.split(readbuffer, "\n")
            readbuffer=temp.pop( )

            # print recieved messages
            print(temp[0])

            # if chat message
            if(temp[0].find("PRIVMSG") > 0 and not temp[0].startswith(":" + self.host)):
                # parse it
                # 1:nick, 2:ident, 3:type, 4:?, 5:message
                msgbuffer = re.search(':(.+)!.+@(.+) (\w+) (.+) :(.+)', temp[0])
                sender  =   msgbuffer.group(1) # sender of message 
                ident   =   msgbuffer.group(2) # used to verify nickname if registered to nickserv
                type    =   msgbuffer.group(3) # we already know this is PRIVMSG
                channel =   msgbuffer.group(4) # where message was written, can also be a nickname
                message =   msgbuffer.group(5).replace("\r\n", "").replace("\r", "").replace("\n", "") # message string

                # if owner sends commands through private message
                if(ident == self.owner and channel == self.nick):
                    if("join" in message):
                        chan = message.split("#")
                        bot_do("join", chan[1])
                    elif("part" in message):
                        chan = message.split("#")
                        bot_do("part", chan[1])
                    elif("quit" in message):
                        bot_do("quit", "")

                # if message seems to be a command
                if(message.startswith("-")):
                    cmd = re.search("(-\w+)", message)
                    cmd = cmd.group(1)
                    try:
                        string = re.search("-\w+\s+(.+)", message)
                        string = string.group(1)
                    except Exception as e:
                        string = ""
                    # if message corresponds to command then execute
                    for command in commands:
                        if(command.name == cmd):
                            command.execute(string, channel, sender)
            # if nickserv complains and bot is a registered user
            elif("NickServ" in temp[0] and "registered" in temp[0] and self.nickserv):
                self.send("", "NickServ", "identify " + self.password)
            # if ping
            elif("PING" in temp[0]):
                self.send("PONG", "", temp[0])

    # make sending messages easier
    def send(self, type, channel, message):
        if(type):
            self.s.send(bytes("%s %s :%s\r\n" % (type, channel, message), "UTF-8"))
            print(type + " " + channel + ": " + message)
        else:
            self.s.send(bytes("PRIVMSG %s :%s\r\n" % (channel, message), "UTF-8"))
            print("PRIVMSG " + channel + ": " + message)

    # graceful quit
    def quit(self):
        self.s.close()
        sys.exit()


# command class
class command:

    def __init__(self, name, helptxt):
        self.name = name
        self.helptxt = helptxt

        commands.append(self)

    def execute(self, string, channel, sender):
        cmd = self.name

        if(cmd == "-g"):
            search_google(string, channel, "web")
        elif(cmd == "-gi"):
            search_google(string, channel, "images")
        elif(cmd == "-imdb"):
            search_imdb(string, channel)
        elif(cmd == "-wp"):
            search_wp(string, channel)
        elif(cmd == "-poem"):
            get_poem(channel)
        elif(cmd == "-quote"):
            get_quote(channel, string)
        elif(cmd == "-help"):
            bot_help(sender)


#----------------------------
# Command functions
#----------------------------
def bot_help(sender):
    vbot.send("", sender, "In case you didn't know, I'm a (beta) bot, shocker. I can do the following:")

    for cmd in commands:
        vbot.send("", sender, cmd.helptxt)

    vbot.send("", sender, "------------------------------------")
    vbot.send("", sender, "Source - https://github.com/rtdmnk/viking-bot")

def bot_do(what, chan):
    if(what == "join"):
        vbot.send("JOIN", "#"+chan, "")
    elif(what == "part"):
        vbot.send("PART", "#"+chan, "")
    elif(what == "quit"):
        vbot.quit()

# replace this with ddg in secret
# https://developers.google.com/image-search/v1/jsondevguide?hl=en
def search_google(search_string, chan, stype):
    try:
        query = urllib.parse.urlencode({'q': search_string})
        url = 'https://ajax.googleapis.com/ajax/services/search/%s?v=1.0&%s' % (stype, query)
        search_response = urllib.request.urlopen(url)
        search_results = search_response.read().decode("utf8")
        results = json.loads(search_results)
        data = results['responseData']['results'][0]['unescapedUrl']
        vbot.send("", chan, data)
    except Exception as e:
        vbot.send("", chan, "Jag fann inget")
        error("search_google", e)
        return

# http://www.omdbapi.com/
def search_imdb(search_string, chan):
    try:
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
    try:
        query = urllib.parse.urlencode({'titles': search_string})
        url = 'https://en.wikipedia.org/w/api.php?format=json&formatversion=2&action=query&prop=extracts&exintro=&explaintext=&redirects&%s' % query
        search_response = urllib.request.urlopen(url)
        search_results = search_response.read().decode("utf8")
        results = json.loads(search_results)

        title = results['query']['pages'][0]['title']
        summary = results['query']['pages'][0]['extract']

        # ugly but works
        try:
            summary = re.match("^(.\.[A-z]\..+?)\.\s", summary).group(1) + "."
        except Exception as e:
            summary = re.match("^(.+?)\.\s", summary).group(1) + "."

        # if summary is over 160 chars, shorten
        if(len(summary) > 160):
            summary = summary[:157] + "..."
        data = summary + " [https://en.wikipedia.org/wiki/" + urllib.parse.quote(title) +"]"
        vbot.send("", chan, data)
    except Exception as e:
        vbot.send("", chan, "Jag fann inge")
        error("search_wp", e)
        return

def get_poem(chan):
    try:
        url = 'http://poems.com/today.php'
        html = urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.find(id="page_title").text
        author = soup.find(id="byline").a.text

        data = "Todays poem: '" + title + "' by " + author + " [" + url + "]"
        vbot.send("", chan, data)
    except Exception as e:
        vbot.send("", chan, "Nåt gick fel")
        error("get_poem", e)
        return

def get_quote(chan, string):
    url = 'http://api.forismatic.com/api/1.0/?method=getQuote&key=457653&format=json&lang=en'
    try:
        # get data
        response = urllib.request.urlopen(url)
        results = response.read().decode("utf8")
        results = json.loads(results)

        # handle data
        quote = results['quoteText']
        quote = re.sub(" $", "", quote)
        author = results['quoteAuthor']
        data = "'" + quote + "' - " + author
        vbot.send("", chan, data)
    except Exception as e:
        vbot.send("", chan, "Nåt gick fel")
        error("get_quote", e)
        return

def error(place, e):
    date = time.strftime("%D-%H:%M")
    # print error to term
    print('\033[1;41m[%s|%s] Caught exception: %s\033[1;m' % (date,place,e))
    if(verbose):
        traceback.print_exc()
    # if log file specified
    try:
        if(vbot.log):
            with open(vbot.log, 'a') as log:
                log.write('[%s|%s] Caught exception: %s\n' % (date,place,e))
    except Exception as e:
        print(e)

def check_args():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:v", ["config="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-v":
            global verbose
            verbose = True
        elif o in ("-c", "--config"):
            global config_file
            config_file = a
        else:
            assert False, "unhandled option"


if __name__ == '__main__':
    # check for command line arguments
    check_args()

    # give life to bot
    vbot = bot()
    vbot.connect()
    vbot.loop()
