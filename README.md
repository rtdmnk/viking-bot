# viking-bot
IRC bot written in Python 3
Command line arguments -v(erbose), prints traceback for exceptions to command line. -c(onfig), point to configuration file (standard is ./vikingBot.conf)

## Requirements
* Python 3
* [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) (only used for command -poem)

## Configuration example
    # Server info 
    host = "irc.server.com"
    # + for ssl, e.g: +6697
    port = 6667
    
    # Bot info
    nick = "VikingIRCBot"
    ident = "info"
    realname = "Amanita Muscaria"
    
    owner = "totalawesomeuser"

    # Logging
    log_file = "viking.log"
    
    # NickServ
    nickserv = True
    password = "supersecret"
