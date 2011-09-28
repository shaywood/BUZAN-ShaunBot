# This is ShaunBot, BUZAN's IRC bot.
# This work is effectively public domain*
# because license enforcement isn't worth the fuss.
# The Python IRC Bot framework used can be found at:
# https://github.com/LukeusMaximus/Python-IRC-Bot-Framework.git
# And ALL credit for that goes to Luke. :)

# This file written by Steven Haywood, steven123456789@hotmail.co.uk

# *: If you insist on a license, you may instead opt to follow the terms of the WTFPL
# If you do so, the full license text would then be as follows:
###########################################################################
# DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE                             #
#                   Version 2, December 2004                              #
#                                                                         #
# Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>                        #
#                                                                         #
# Everyone is permitted to copy and distribute verbatim or modified       #
# copies of this license document, and changing it is allowed as long     #
# as the name is changed.                                                 #
#                                                                         #
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE                  #
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION       #
#                                                                         #
#  0. You just DO WHAT THE FUCK YOU WANT TO.                              #
###########################################################################

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
STATE_FILE = 'state' # For saving data in between restarts.

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
# being permitted to do anything (unless the commmand permits anyone to execute it)
# And you must confirm the alias by switching to the alias, IDing with NickServ if required, then
# issuing !confirmalias

# You may issue !rejectalias, which does the opposite.

# !Aliases // Lists the nicknames within the NICK GROUP belonging to the sender
# If the sender has no group, then it finds the NICK GROUP which contains the sender,
# and informs them what their "master" nick is as well.

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
# !viewgroups

# EXCEPT:
# The hardcoded ADMINS group which cannot be modified.
# The hardcoded FLAT_MEMBERS group, because we use this to run our Minecraft Server.
# (Are you honestly surprised?)

# Command names:
CMD_GET_ZTL = "!threat"
CMD_SET_ZTL = CMD_GET_ZTL # yes, really.
CMD_THREAT_PLUS = "!threat+"
CMD_THREAT_MINUS = "!threat-"

CMD_NERF_SOCIAL = "!nerfsocial"
CMD_PUB_SOCIAL = "!pubsocial"
CMD_HELP = "!help"
CMD_BLARG = "!blarg"
CMD_QUIT = "!quit"
CMD_RESTART = "!restart"
CMD_LOGGING = "!logging"
CMD_START_LOGGING = "!startlog"
CMD_STOP_LOGGING = "!stoplog"
CMD_ABOUT = "!about"
CMD_TELL = "!tell"

CMD_MC_RESTART = "!mcrestart"
CMD_MC_STOP = "!mcstop"
CMD_MC_START = "!mcstart"
CMD_MC_STATUS = "!mcstatus"
CMD_MC_CONSOLE = "!mcconsole"

# Minecraft related stuff:
MINECRAFT_DIR = "~/Downloads/minecraft-server/"
MINECRAFT_BACKUP_DIR = "~/Desktop/mcbackup"
MINECRAFT_BACKUP_INTERVAL = 10 * 60

MINECRAFT_SERVER_COMMAND = "java -Xmx1024M -Xms1024M -jar " + MINECRAFT_DIR + "minecraft_server.jar nogui"
MINECRAFT_BACKUP_COMMAND = "cp -u -r -f " + MINECRAFT_DIR + "* " + MINECRAFT_BACKUP_DIR

# imports:
from ircbotframe import ircBot
from sys import exit, argv
import subprocess # for restarting ourselves
from time import asctime # for timestamps
import random # for trolling Boff - I mean this.
import minecraftserver # <OWL>
from datetime import datetime, timedelta
import threading # for regular backups

# A few more useful constants:
THIRTY_DAYS = timedelta.timedelta(days = 30)

class IRCNickGroup:
	""" Class to represent a NICK GROUP as defined above. """	
	# Implements the "in" operator:	
	def __contains__(self, Nickname):
		return Nickname in self.Nicks

	def __init__(self, Nickname):
		self.Nicks = []
		self.Nicks.append(Nickname)
		
		self.OriginalNick = Nickname
		self.LastSeen = datetime.now()

	def AddNickname(self, Nickname):
		if Nickname not in self.Nicks:			
			self.Nicks.append(Nickname)
			# Keep this list sorted.
			self.Nicks.sort(key=str.lower)

			return True
		else:	
			return False
	
	def RemoveNickname(self, Nickname):
		if Nickname in self.Nicks:
			self.Nicks.remove(Nickname)
			self.Nicks.sort(key=str.lower)

			return True
		else:
			return False

	def GetLastSeen(self):
		return self.LastSeen

	def GetMasterNickname(self):
		return self.OriginalNick

class IRCAccessGroup:
	""" Class to represent an ACCESS GROUP as defined above """	
	def __contains__(self, Nickname):	
		for Group in self.NickGroups:
			if Nickname in Group:
				return True

		return False	

	def __init__(self, GroupName):
		self.GroupName = GroupName
	
		self.NickGroups = [] # Contains instances of IRCNickGroup	
	
	def AddNickGroup(self, NickGroup):
		if NickGroup not in self.NickGroups:
			self.NickGroups.append(NickGroup)
		
		# cannot fail:		
		return True

	def RemoveNickGroup(self, NickGroup):
		if NickGroup in self.NickGroups:
			self.remove(NickGroups)

			return True
		else:
			return False
		
class CMDAccessGroup:
	""" Class to represent a group of ACCESS GROUPS, used by commands
		to "remember" which people are permitted to use them.

		if this collection is empty (ie: len(<CMDAccessGroup>) = 0), then
		anyone is permitted to use it.  """

	def __len__(self):
		return len(self.AccessGroups)

	def __contains__(self, Nickname):
		if len(self) != 0:
			for Group in self.AccessGroups:
				if Nickname in Group:
					return True

			# Nickname is not within this CMDAccessGroup:
			return False
		else:
			# No IRCAccessGroups => anyone can use it.
			# Therefore we return True. This is DELIBERATE.
			return True

	def __init__(self):
		self.AccessGroups = []

	def AddAccessGroup(self, AccessGroup):
		if AccessGroup not in self.AccessGroups:
			self.AccessGroups.append(AccessGroup)

		# Cannot fail:		
		return True

	def RemoveAccessGroup(self, AccessGroup):
		if Accessgroup in self.AccessGroups:
			self.AccessGroups.remove(AccessGroup)

			return True
		else:
			return False

	def AllowAnyone(self):
		return len(self) == 0

class OfflineMessage:
	""" Class to encapsulate an offline message. Used by !tell
		and also generated by !addalias for alias confirmation. """
	def __str__(self):
		# Whilst this might be slow, the expression is hard enough to read:

		# Format returned is: "On Wed, 1 of Jan 2011 at 21:31 CarrierII said: NYAN?!"

		S = "On " + self.TimeSent.strftime("%a, %d of %b %Y")
		S = S + " at " + self.TimeSent.strftime("%H:%M")
		S = S + " " + self.Sender + "said: " + self.Message
	
		return S			
	
	def __init__(self, Sender, Dest, Message):
		self.Sender = SenderNick
		self.Dest = DestNick
		self.Message = Message
		self.TimeSent = datetime.now()

	def GetDestNick(self):
		return self.Dest

# Some final constants:
# Default command listing.
# Note the CMD_GROUPS section will be used if there is no state file.
# (ie: the bot is starting for the first time)

CMD_CMD = 0
CMD_FUNC = 1
CMD_GROUPS = 2
CMD_USAGE = 3
CMD_HELP = 4

class ShaunBot:
	# Commands to do:
	# !insult <nick> <style>, where style can be any of... :D
	# !committee - gives the sender committee contact info. This needs to be settable, so I need a committee group.
	# !meet <nick> - adds <nick> to the bot's list of known people, if it isn't in there already.

	# CMD, CLASS, GROUPS, USAGE, HELP
	COMMANDS = [
		[CMD_GET_ZTL, GetZTLCommand, [], CMD_GET_ZTL, "Gets the current Zombie Threat Level"],	
		[CMD_SET_ZTL, SetZTLCommand, [ADMINS], "!threat+, !threat-, !threat N", "Sets the Zombie Threat Level"],
		[CMD_NERF_SOCIAL, GetNerfSocialCommand, [], CMD_NERF_SOCIAL, "Gets the info about the next Nerf Social"],
		[CMD_NERF_SOCIAL, SetNerfSocialCommand, [ADMINS], "!nerfsocial <helpful and informative text>", "Sets the Nerf Social info"],
		[CMD_QUIT, QuitCommand, [ADMINS], "!quit <message>", "Makes the bot quit. Requires a MANUAL restart"],
		[CMD_RESTART, RestartCommand, [ADMINS], "!restart <message>", "Restarts the bot"],
		[CMD_BLARG, BlargCommand, [], "", ""],
		[CMD_ABOUT, AboutCommand, [], CMD_ABOUT, "Returns info about the bot"],
		[CMD_LOGGING, LoggingCommand, [], CMD_LOGGING, "Indicates whether or not the bot is currently logging"],
		[CMD_START_LOGGING, StartLogCommand, [ADMINS], CMD_START_LOGGING, "Makes the bot log all messages it can see"],
		[CMD_STOP_LOGGING, StopLogCommand, [ADMINS], CMD_STOP_LOGGING, "Stops the bot logging messages"],
		[CMD_HELP, GeneralHelpCommand, [], CMD_HELP, "Returns a list of commands"],
		[CMD_HELP, SpecificHelpCommand, [], CMD_HELP + " <command, no !>", "Returns help about the specified command"],
		[CMD_PUB_SOCIAL, GetPubSocialCommand, [], CMD_PUB_SOCIAL, "Gets the info about the next pub social"],
		[CMD_PUB_SOCIAL, SetPubSocialCommand, [ADMINS], CMD_PUB_SOCIAL + " <helpful and informative text>", "Sets the Pub Social info"],
		[CMD_TELL, TellCommand, [], CMD_TELL + " <nickname> <message>", "Gives message to nickname when nickname next signs on"],
		[CMD_MEET, MeetCommand, [], CMD_MEET + " <nickname>", "Prevents the bot from greeting people"],
		# Flat minecraft server related commands:
		[CMD_MC_RESTART, MCRestartCommand, [FLAT_MEMBERS], CMD_MC_RESTART, "Restarts the Minecraft server instance, if it is running"],
		[CMD_MC_STOP, MCStopCommand, [FLAT_MEMBERS], CMD_MC_STOP, "Stops the Minecraft server instance, if it is running"],
		[CMD_MC_START, MCStartCommand, [FLAT_MEMBERS], CMD_MC_START, "Starts the Minecraft server, if it isn't running"],
		[CMD_MC_STATUS, MCStatusCommand, [FLAT_MEMBERS], CMD_MC_STATUS, "Returns the status of the Minecraft server instance"],
		[CMD_MC_CONSOLE, MCConsoleCommand, [FLAT_MEMBERS], CMD_MC_CONSOLE + " <command, as issued to the MC server console> ", 
										"Issues the command directly to the MC server's StdIn. This might cause explosions. :)"]
		]
	

	def SayToChannel(self, Message):
		self.say(CHANNEL, Message)	
		
	def Run(self):
		# Do stuff:
		pass
		

		
	
#############################################
# Main program:
ShaunBot = 


