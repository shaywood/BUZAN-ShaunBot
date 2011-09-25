# This is ShaunBot, BUZAN's IRC bot.
# This work is effectively public domain
# because license enforcement isn't worth the fuss.
# The Python IRC Bot framework used can be found at:
# https://github.com/LukeusMaximus/Python-IRC-Bot-Framework.git
# And full credit for that goes to Luke. :)

# This file written by Steven Haywood, steven123456789@hotmail.co.uk

# "Constants":
# IRC:
NETWORK = "irc.synirc.net"
PORT = 6667
CHANNEL = "#buzan"
NICKNAME = "ShaunBot"
DESCRIPTION = "ZomPoc Tracking Bot"
NICKSERV_PASS = "Nice try, but I actually read this from the command line args..." 

# meta:
VERSION = "0.9 Beta - New Framework - HerpaDerpa Ninja Fire Build" # Don't ask.
AUTHORS = "CarrierII, Lukeus_Maximus"
ABOUT = "I am ShaunBot, Zombie Robot Ghost" # Don't tell, for that matter.

# Command for restarting self:
COMMAND_FOR_SELF = "..\launcher.sh" # Shell script which pulls updates and then runs the bot again

BACKUP_INTERVAL = 60 * 60 * 24 # once a day (value in seconds)

# !tell command has a message limit, which is enforced for all nicks in a group.
PER_NICK_MESSAGE_LIMIT = 20

# Local files:
LOG_FILE = 'log'
CMD_LOG_FILE = 'cmd_log'
STATE_FILE = 'state' # For saving data in between restarts. pickle ftw!




