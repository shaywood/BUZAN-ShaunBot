# This is ShaunBot, BUZAN's IRC bot.
# This work is effectively public domain*
# because license enforcement isn't worth the fuss.
# The Python IRC Bot framework used can be found at:
# https://github.com/LukeusMaximus/Python-IRC-Bot-Framework.git
# And ALL credit for that goes to Luke. :)

# This file written by Steven Haywood, steven123456789@hotmail.co.uk

# *: If you insist on a license, you may opt to follow the terms of the
# WTFPL - Do What the Fuck You Want To Public License
# Full license would then be as follows:
# DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                   Version 2, December 2004

# Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.

#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

#  0. You just DO WHAT THE FUCK YOU WANT TO.

# Happy now?

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

# Command grouping:
# Each PERSON has 1 or more NICKS. (For instance, I use CarrierII and EtherealII as a backup)
# So give every PERSON a NICK GROUP. 
# A NICK GROUP is created for every unique name the bot encounters,
# and is destroyed after 30 days of never being seen again. (ie, /none/ of the nicks in it are seen in 30 days)
# People can group their nicknames by using
# !AddAlias <nick> // Tells the bot that <nick> is the same person as Sender.
# This is rejected if:
# 1) <nick> is already in another group.
# 2) Sender's nickname is not registered with NickServ
# In order to prevent abuse - (eg: "<CarrierII> !AddAlias Boff") - all nicknames are checked against NickServ before
# being permitted to do anything (unless the commmand permits anyone)

# !RemoveAlias <nick> // Tells the bot the sender is /not/ the same person as <nick> (removes them from that group)

# (If NickServ implements querying other people's group lists, that will be used instead)

# An ACCESS GROUP is a group of NICK GROUPS (no, that isn't an error).
# Each COMMAND has one or more ACCESS GROUPS. You must be an auth'd member of one of the NICK GROUPS
# mentioned in one of the ACCESS GROUPS in order to execute the command.

# This is insanely slow. :D

# ACCESS GROUPS can be manipulated using:
# !addtogroup <nick> <group name>
# !removefromgroup <nick> <group name>
# !creategroup <group name>
# !destroygroup <group name>
# !setcommandgroup <command, no !> <group name> # some exceptions apply for security reasons

# EXCEPT:
# The hardcoded ADMINS group which cannot be modified.



