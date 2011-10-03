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

# Imports:
from ircbotframe import ircBot
from sys import exit, argv
import subprocess # for restarting ourselves
from time import asctime # for timestamps
import random # for trolling Boff - I mean this.
import minecraftserver # <OWL>
from datetime import datetime, timedelta
import threading # for regular backups

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
COMMAND_FOR_SELF = "./relauncher.sh" # Shell script which pulls updates and then runs the bot again

BACKUP_INTERVAL = 60 * 60 # once an hour (value in seconds)

# !tell command has a message limit, which is enforced for all nicks in a group.
PER_NICK_MESSAGE_LIMIT = 20

# Local files:
LOG_FILE = 'log'
CMD_LOG_FILE = 'cmd_log'
STATE_FILE = 'state' # For saving data in between restarts.

# Misc:
ZOMBIE_THREAT_LEVELS = ['Low', 'Guarded', 'Medium', 'High', "Contact Helena, that is your only hope now..."]

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
ADMINS = [["CarrierII"], ["LaptopBoff", "Boff"], ["Spud"]]

FLAT_MEMBERS = [["CarrierII"], ["Lukeus_Maximus"], ["Molubdos"]] # Add PikminDoctor when I know his nick is good. :)

# Command names:
CMD_GET_ZTL = "!threat"
CMD_SET_ZTL = "!threat " # yes, really. That space is deliberate.
CMD_THREAT_PLUS = "!threat+"
CMD_THREAT_MINUS = "!threat-"

CMD_GET_NERF_SOCIAL = "!nerfsocial"
CMD_SET_NERF_SOCIAL = "!nerfsocial "
CMD_GET_PUB_SOCIAL = "!pubsocial"
CMD_SET_PUB_SOCIAL = "!pubsocial "
CMD_HELP = "!help"
CMD_SPECIFIC_HELP = "!help "
CMD_BLARG = "!blarg"
CMD_QUIT = "!quit"
CMD_RESTART = "!restart"
CMD_LOGGING = "!logging"
CMD_START_LOGGING = "!startlog"
CMD_STOP_LOGGING = "!stoplog"
CMD_ABOUT = "!about"
CMD_TELL = "!tell"
CMD_MEET = "!meet"

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

# A few more useful constants:
THIRTY_DAYS = timedelta(days = 30)
# This MUST NOT BE CHANGED!
# Format eg: hh:mm:ss--dd/mm/yyyy
TIMESTAMP_FORMAT = "%H:%M:%S--%d/%m/%Y"

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
		S = S + " " + self.Sender.GetMasterNickname() + " said: " + self.Message
	
		return S			
	
	def __init__(self, SendersGrp, Dest, Message):
		self.Sender = SendersGrp
		self.Dest = Dest
		self.Message = Message
		self.TimeSent = datetime.now()

	def GetDestNick(self):
		return self.Dest

class OfflineMessageList:
	def __init__(self):
		self.Messages = []

	def AddMessage(self, OfflineMsg):
		""" Returns True/False based on success.
			Adds OfflineMsg to the internal list IIF the sender is not breaking the message limit """
		MsgCount = 0
		for LocalMsg in self.Messages:
			if OfflineMsg.Sender == LocalMsg.Sender:
				MsgCount = MsgCount + 1

		if MsgCount <= PER_NICK_MESSAGE_LIMIT:
			self.Messages.append(OfflineMsg)
			return True
		else:
			return False

	def CheckForMessages(self, NickGrp):
		""" Returns a list of OfflineMessage instances intended for NickGrp """
		Result = []
		
		for Msg in self.Messages:
			if Msg.Sender == NickGrp:
				Result.append(Msg)
				self.Messages.remove(Msg) # Remove that message.

		return Result # Ya, rly.

# Some final constants:
# Default command listing.
# Note the CMD_GROUPS section will be used if there is no state file.
# (ie: the bot is starting for the first time)

CMD_CMD = 0
CMD_FUNC = 1
CMD_GROUPS = 2
CMD_USAGE = 3
CMD_HELP_TEXT = 4

def GetHelpMessage(Cmd):
	return Cmd[CMD_USAGE] + " - " + Cmd[CMD_HELP_TEXT]

def OnAuthFailure(Bot):
	# Do nothing. Useful as I have to specify it... :/
	return

def OnAuthSuccess(Bot, Dest, Message):
	# Sends Message to Dest:
	Bot.say(Dest, Message)

# IRC binding implementations:
def OnCmdAuthSuccess(Bot, ShaunBotInst, Sender, ReplyTo, Headers, Message, Cmd):
	Cmd[CMD_FUNC](ShaunBotInst, Sender, ReplyTo, Headers, Message, Cmd) # Call the function, all auth already done.	

class ShaunBot:
	# Utility functions:
	def Say(self, Dests, Message):
		for Dest in Dests:
			self.Bot.say(Dest, Message)
	
	def Log(self, Sender, Dest, Message):
		LogStr = asctime() + "<" + Sender + "> " + Dest + ": " + Message		
		print LogStr

		if self.LogFile != None:
			self.LogFile.write(LogStr + '\n')	

		NickGrp = self.GetGroupOfNickname(Sender)
		NickGrp.LastSeen = datetime.now()

	# Nickname and NickGroup function(s):
	def GetGroupOfNickname(self, Nickname):
		""" Returns the IRCNickGroup associated with Nickname.
			Creates that group if it does not exist """
		# This needs to be faster, but that's hard. :(
		for Grp in self.Nickgroups:
			if Nickname in Grp:
				return Grp
		
		Grp = IRCNickGroup(Nickname)		
		self.Nickgroups.append(Grp)
		self.NewestNickGroup = Grp

		return Grp

	def GetAccessGroup(self, GroupName):
		""" Gets the IRCAccessGroup named in the parameter.
			if it does not exist, None is returned """
		for Grp in self.Groups:
			if Grp.GroupName == GroupName:
				return Grp

		return None

	# Private functions:
	def I_GetZTL(self):	
		# Returns correctly formatted ZTL string:
		if self.ZTL != len(ZOMBIE_THREAT_LEVELS) - 1:
			return "Zombie Threat Level: " + ZOMBIE_THREAT_LEVELS[self.ZTL]
		else: # The highest one has grammar that breaks if returned as above, thus:
			return ZOMBIE_THREAT_LEVELS[self.ZTL]

	def I_SetZTL(self, NewZTL, UserProvidedValue, Command):						
		# Returns the string to be said by the bot as a result of this attempt to change ZTL		
		# If UserProvidedValue, return usage, else,
		# return silly messages about how relaxed/stressed the bot it based on NewZTL:

		if NewZTL < 0:
			if UserProvidedValue:
				return Command[CMD_USAGE]
			else:
				return "Cannot lower the zombie threat level because I am too relaxed..."
		elif NewZTL >= len(ZOMBIE_THREAT_LEVELS):
			if UserProvidedValue:
				return Command[CMD_USAGE]
			else:
				return "Cannot raise the zombie threat level because there are zombies at the door!!"
		elif NewZTL == self.ZTL:
			return "The Zombie Threat Level remains at: " + ZOMBIE_THREAT_LEVELS[self.ZTL]
		elif NewZTL > self.ZTL:			
			self.ZTL = NewZTL
			
			if self.ZTL != len(ZOMBIE_THREAT_LEVELS) - 1:			
				return "Warning! Zombie Threat Level raised to: " + ZOMBIE_THREAT_LEVELS[self.ZTL]
			else: # See above remark about grammar:
				return ZOMBIE_THREAT_LEVELS[self.ZTL]
		else: # NewZTL < ZTL:
			self.ZTL = NewZTL			
			return "Good news! Zombie Threat Level lowered to: " + ZOMBIE_THREAT_LEVELS[self.ZTL]

	# Command implementations:	
	def GetZTLCommand(self, Sender, ReplyTo, Headers, Message, Command):		
		self.Say([ReplyTo], self.I_GetZTL())

		return True		
	
	def SetZTLCommand(self, Sender, ReplyTo, Headers, Message, Command):
		# Changes to the ZTL get relayed to the channel, even if issued in private		
		if Message == CMD_THREAT_PLUS:
			self.Say([CHANNEL], self.I_SetZTL(self.ZTL + 1, False, Command))	
		elif Message == CMD_THREAT_MINUS:
			self.Say([CHANNEL], self.I_SetZTL(self.ZTL - 1, False, Command))
		else:
			# Should be of form !threat N, where N is an integer within the limits of ZOMBIE_THREAT_LEVELS
			# Deal with it:		
			Parts = Message.split(' ')
			if Parts[0] + ' ' == CMD_SET_ZTL:
				try:
					NewZTL = int(Parts[1])
					self.Say([CHANNEL], self.I_SetZTL(NewZTL, True, Command))
				except:
					self.Say([Sender], Command[CMD_USAGE])
			else:
				return False # Couldn't make sense of this at all!!
				# (eg: !threatargleflargleblargle) - o0

		return True
	
	def GetNerfSocialCommand(self, Sender, ReplyTo, Headers, Message, Command):
		self.Say([ReplyTo], "The next nerf social will be: " + self.NerfSocial)	

		return True
		
	def SetNerfSocialCommand(self, Sender, ReplyTo, Headers, Message, Command):	
		# is Message of the form !nerfsocial <string containing new nerf social>?
		NewNerfSocial = Message[len(CMD_GET_NERF_SOCIAL) + 1:]
			
		if NewNerfSocial != "":
			self.NerfSocial = NewNerfSocial
			# Nerf Social changes should be relayed to the channel:										
			self.Say([CHANNEL], "The next Nerf Social will now be: " + self.NerfSocial)
			
			return True
		else:
			return False

	def GetPubSocialCommand(self, Sender, ReplyTo, Headers, Message, Command):
		self.Say([ReplyTo], "The next pub social will be: " + self.PubSocial)	

		return True		

	def SetPubSocialCommand(self, Sender, ReplyTo, Headers, Message, Command):	
		# Of form !pubsocial <string containing new pub social>?
		NewPubSocial = Message[len(CMD_GET_PUB_SOCIAL) + 1:]
		if NewPubSocial != "":
			self.PubSocial = NewPubSocial
			# Pub Social changes should be relayed to the channel:										
			self.Say([CHANNEL], "The next Pub Social will now be: " + self.PubSocial)
			
			return True
		else:
			return False
	
	def GeneralHelpCommand(self, Sender, ReplyTo, Headers, Message, Command):	
		for Cmd in self.CommandList.values():
			if Cmd[CMD_HELP_TEXT] != '': # Hidden commands have no help			
				if Cmd[CMD_GROUPS].AllowAnyone():
					self.Say([Sender], GetHelpMessage(Cmd))
				else:
					# Check if sender is permitted to see this command:
					if Sender in Cmd[CMD_GROUPS]:
						self.Bot.identify(Sender, OnAuthSuccess, [Sender, GetHelpMessage(Cmd)], OnAuthFailure, [])
						# Help message will be sent to sender if auth succeeded.		

		return True

	def SpecificHelpCommand(self, Sender, ReplyTo, Headers, Message, Command):
		Sections = Message.split(' ')
		if len(Sections) < 2 or Sections[1] == '':
			self.Say([Sender], GetHelpMessage(Command)) # Show them how to use this (help) command
			return True

		Sections[1] = '!' + Sections[1].lower()

		Cmd = self.CommandList.get(Sections[1], None)

		if Cmd != None:						
			if Cmd[CMD_HELP_TEXT] != '': # Hidden commands have no help
				# Help wanted for this command:
				if Cmd[CMD_GROUPS].AllowAnyone():
					self.Say([Sender], GetHelpMessage(Cmd))
				else:
					if Sender in Cmd[CMD_GROUPS]:
						self.Bot.identify(Sender, OnAuthSuccess, [Sender, GetHelpMessage(Cmd)], OnAuthFailure, [])
				
		else:
			self.Say([Sender], "I'm sorry, but there is no command \"" + Sections[1] + "\", if you think there should be, contact CarrierII")

		return True

	def BlargCommand(self, Sender, ReplyTo, Headers, Message, Command):
		self.Say([ReplyTo], "BLARG!")

		return True

	def QuitCommand(self, Sender, ReplyTo, Headers, Message, Command):
		QuitMsg = Message[len(CMD_QUIT) + 1:]	
		
		if QuitMsg == '':
			QuitMsg = "Quiting because " + Sender + " told me to."
	
		self.Bot.disconnect(QuitMsg)	

		self.RestartSelf = False
		self.Bot.stop() # Causes Bot.run() to return

		return True
	
	def RestartCommand(self, Sender, ReplyTo, Headers, Message, Command):
		QuitMsg = Message[len(CMD_RESTART) + 1:]
		if QuitMsg == '':
			QuitMsg = "Restarting because " + Sender + " told me to."

		self.Bot.disconnect(QuitMsg)
		
		self.RestartSelf = True		
		self.Bot.stop()

		return True

	def LoggingCommand(self, Sender, ReplyTo, Headers, Message, Command):		
		if (self.LogFile != None) and (not self.LogFile.closed):
			# Logging is channel-level info:			
			self.Say([CHANNEL], "I am currently logging this channel.")
		else:
			self.Say([CHANNEL], "No logging in progress.")    

		return True

	def StartLogCommand(self, Sender, ReplyTo, Headers, Message, Command):
		if self.LogFile == None:
			try:
				self.LogFile = open(LOG_FILE, 'a')
				self.Say([CHANNEL], "Logging started by " + Sender)      
			except:
				self.LogFile = None
				self.Say([Sender], "Error - Unable to start logging at this time!")
		else:
			self.Say([CHANNEL], "I am already logging!")

		return True
		
	def StopLogCommand(self, Sender, ReplyTo, Headers, Message, Command):
		if self.LogFile != None:
			try:
				self.Say([CHANNEL], "Logging stopped by " + whoFrom)
			  
				self.LogFile.flush()
				self.LogFile.close()
				self.LogFile = None        
			except:
				self.Say([Sender], "Error - Unable to stop logging at this time!")			
		else:
			self.Say([CHANNEL], "I am not currently logging!") 
		
		return True

	def AboutCommand(self, Sender, ReplyTo, Headers, Message, Command):
		# Always dump this in PM, because spam		
		self.Say([Sender], ABOUT)
		self.Say([Sender], "Version: " + VERSION)
		self.Say([Sender], "Written by: " + AUTHORS)

		return True

	def TellCommand(self, Sender, ReplyTo, Headers, Message, Command):
		Sections = Message.split(' ')
		if len(Sections) < 3:
			return False

		if Sections[0] != CMD_TELL:
			return False

		# Create the offline message:
		SendersGrp = self.GetGroupOfNickname(Sender)
		Dest = Sections[1]
	
		Message = ''	
		# I think there is a faster way to do this?		
		for i in range(2, len(Sections)):
			Message = Message + Sections[i] + ' '		

		OfflineMsg = OfflineMessage(SendersGrp, Dest, Message)		

		if self.OfflineMessageList.AddMessage(OfflineMsg):
			self.Say([Sender], "Your message will be delivered the next time I see " + Dest)
		else:
			self.Say([Sender], "You cannot send any more messages until old ones are delivered or expire!")

		return True

	def	MeetCommand(self, Sender, ReplyTo, Headers, Message, Command):
		Sections = Message.split(' ')
		if len(Sections) < 2 or Sections[0] != CMD_MEET:
			return False

		# Expecting of form "!meet <nickname>", as the bot will have already met someone talking to it.
		self.GetGroupOfNickname(Sections[1]) # This is all you need to do. ;)
		
		return True			

	# Commands to do:
	# !insult <nick> <style>, where style can be any of... :D
	# (Related: !addinsult <style> <text, with %n as nickname; !removeinsult <style> <enough text to uniquely ID it>)
	# !committee - gives the sender committee contact info. This needs to be settable, so I need a committee group and a place to dump this info.
	# !meet <nick> - adds <nick> to the bot's list of known people, if it isn't in there already.
	
	# CMD, CLASS, GROUPS, USAGE, HELP
	# This is used do to some initialisation, although the groups value gets overridden by any state file info.
	DEFAULT_COMMANDS = [
		[CMD_GET_ZTL, GetZTLCommand, [], CMD_GET_ZTL, "Gets the current Zombie Threat Level"],	
		[CMD_SET_ZTL, SetZTLCommand, ["ADMINS"], "!threat+, !threat-, !threat N", "Sets the Zombie Threat Level"],
		[CMD_GET_NERF_SOCIAL, GetNerfSocialCommand, [], CMD_GET_NERF_SOCIAL, "Gets the info about the next Nerf Social"],
		[CMD_SET_NERF_SOCIAL, SetNerfSocialCommand, ["ADMINS"], CMD_GET_NERF_SOCIAL + " <helpful and informative text>", "Sets the Nerf Social info"],
		[CMD_QUIT, QuitCommand, ["ADMINS"], "!quit <message>", "Makes the bot quit. Requires a MANUAL restart"],
		[CMD_RESTART, RestartCommand, ["ADMINS"], "!restart <message>", "Restarts the bot"],
		[CMD_BLARG, BlargCommand, [], "", ""],
		[CMD_ABOUT, AboutCommand, [], CMD_ABOUT, "Returns info about the bot"],
		[CMD_LOGGING, LoggingCommand, [], CMD_LOGGING, "Indicates whether or not the bot is currently logging"],
		[CMD_START_LOGGING, StartLogCommand, ["ADMINS"], CMD_START_LOGGING, "Makes the bot log all messages it can see"],
		[CMD_STOP_LOGGING, StopLogCommand, ["ADMINS"], CMD_STOP_LOGGING, "Stops the bot logging messages"],
		[CMD_HELP, GeneralHelpCommand, [], CMD_HELP, "Returns a list of commands"],
		[CMD_SPECIFIC_HELP, SpecificHelpCommand, [], CMD_HELP + " <command, no !>", "Returns help about the specified command"],
		[CMD_GET_PUB_SOCIAL, GetPubSocialCommand, [], CMD_GET_PUB_SOCIAL, "Gets the info about the next pub social"],
		[CMD_SET_PUB_SOCIAL, SetPubSocialCommand, ["ADMINS"], CMD_GET_PUB_SOCIAL + " <helpful and informative text>", "Sets the Pub Social info"],
		[CMD_TELL, TellCommand, [], CMD_TELL + " <nickname> <message>", "Gives message to nickname when nickname next signs on"],
		[CMD_MEET, MeetCommand, [], CMD_MEET + " <nickname>", "Prevents the bot from greeting people"]#,
		# Flat minecraft server related commands:
		#[CMD_MC_RESTART, MCRestartCommand, [FLAT_MEMBERS], CMD_MC_RESTART, "Restarts the Minecraft server instance, if it is running"],
		#[CMD_MC_STOP, MCStopCommand, [FLAT_MEMBERS], CMD_MC_STOP, "Stops the Minecraft server instance, if it is running"],
		#[CMD_MC_START, MCStartCommand, [FLAT_MEMBERS], CMD_MC_START, "Starts the Minecraft server, if it isn't running"],
		#[CMD_MC_STATUS, MCStatusCommand, [FLAT_MEMBERS], CMD_MC_STATUS, "Returns the status of the Minecraft server instance"],
		#[CMD_MC_CONSOLE, MCConsoleCommand, [FLAT_MEMBERS], CMD_MC_CONSOLE + " <command, as issued to the MC server console> ", 
		#								"Issues the command directly to the MC server's StdIn. This might cause explosions. :)"]
		]
	
	def WriteStateFile(self):
		try:		
			StateFile = open(STATE_FILE, 'w')
		
			#print "Writing ZTL"			
			StateFile.write("ZTL=" + str(self.ZTL) + '\n')
			#print "Writing NerfSocial"
			StateFile.write("NerfSocial=" + self.NerfSocial + '\n')
			#print "Writing PubSocial"
			StateFile.write("PubSocial=" + self.PubSocial + '\n')
	
			# Now special info:
			#print "Writing Logging"
			Logging = (self.LogFile != None)
			StateFile.write("Logging=" + str(Logging) + '\n')
			
			# All dumps of classes wrap strings in quotes.
			# Quotes do not occur in the strings they are wrapping.
			# All fields are thus separated by: ',', with the contents of each field between "'s

			# Must dump nicknames before command groups and offline messages, or else fault on reading:
			# Nick group format is: NickGroup=<timestamp>,<MasterNickname>,<Nickname 0>,<Nickname N>, etc
			for NickGrp in self.Nickgroups:
				# Dump /all/ timestamps in format described by TIMESTAMP_FORMAT			
				#print "Dumping Nickgroup: " + NickGrp.GetMasterNickname()
				StateFile.write('NickGroup="' + NickGrp.LastSeen.strftime(TIMESTAMP_FORMAT) + '"')
				StateFile.write(",\"" + NickGrp.GetMasterNickname() + '"')
				for Nick in NickGrp.Nicks:
					StateFile.write(",\"" + Nick + '"')

				StateFile.write('\n')
					
			# Now offline messages:
			# Format is: OfflineMessage=<Sender's Group's MasterNickname>,<Dest nick>,<Message>,<Timestamp>
			for Msg in self.OfflineMessageList.Messages:
				#print "Dumping OfflineMessage belonging to: " + Msg.Sender.GetMasterNickname()				
				StateFile.write("OfflineMessage=\"" + Msg.Sender.GetMasterNickname() + '"')
				StateFile.write(",\"" + Msg.Dest + '"')
				StateFile.write(",\"" + Msg.Message + '"')
				StateFile.write(",\"" + Msg.TimeSent.strftime(TIMESTAMP_FORMAT)  + '"\n')

			# Now Groups:
			# Format is: "AccessGroup=<Group Name>,<Nick group MasterNickname 0>,<Nick group MasterNickname N> 
			for Grp in self.Groups:
				#print "Dumping AccessGroup: " + Grp.GroupName				
				StateFile.write('AccessGroup="' + Grp.GroupName + '"')
				for NickGrp in Grp.NickGroups:
					StateFile.write(",\"" + NickGrp.GetMasterNickname() + '"')

				StateFile.write('\n')

			# Now new command groupings:
			# FIXME

			StateFile.flush()
			StateFile.close()
		except:
			print "Failed to write statefile!"		

	def ReadStateFile(self):
		try:
			StateFile = open(STATE_FILE, 'r')
			Lines = StateFile.readlines()
			StateFile.close()
		except:
			print "Couldn't use state file, resorting to defaults!"
			return
		
		print "Parsing state file..."		
		if len(Lines) == 0:
			print "Empty state file, resorting to defaults!"
			return
		
		for Line in Lines:
			try:			
				#print "Parsing line: " + Line
				
				LineSections = Line.split('=')
				
				if len(LineSections) != 2:
					print "Malformed line: " + Line
					print "Skipping"
					continue

				if LineSections[0] == "ZTL":
					self.ZTL = int(LineSections[1])
					#print "Set ZTL = " + str(self.ZTL)

				elif LineSections[0] == "NerfSocial":
					self.NerfSocial = LineSections[1].strip('\n')
					#print "Set NerfSo	109.157.232.174cial = " + self.NerfSocial

				elif LineSections[0] == "PubSocial":
					self.PubSocial = LineSections[1].strip('\n')
					#print "Set PubSocial = " + self.PubSocial

				elif LineSections[0] == "Logging":
					if LineSections[1] == "True\n":					
						try:
							self.LogFile = open(LOG_FILE, 'a')
							print "Logging is initially ON!"
						except:
							print "Encountered an exception attempting to start logging, no longer logging!"
					else:
						print "Logging is initially OFF!"

				elif LineSections[0] == "NickGroup":
					# Format is: NickGroup=<timestamp>,<MasterNickname>,<Nickname 0>,<Nickname N>, etc
					Params = LineSections[1].split(',')
					for i in range(len(Params)):
						Params[i] = Params[i].strip('\n').strip('"')
						
					# Params now corresponds to the order in the format line:
					if len(Params) < 2:
						print "Bad Nickgroup entry, skipping!"
						print LineSections[1]
						continue
							
					print "Creating a nickgroup for: " + Params[1]
					NewNickGrp = self.GetGroupOfNickname(Params[1])

					NewNickGrp.LastSeen = datetime.strptime(Params[0], TIMESTAMP_FORMAT)
					for i in range(2, len(Params)):
						#print "Adding " + Params[i] + " to that group..."						
						NewNickGrp.AddNickname(Params[i])
							#print "Actually added them."
					
					self.NewestNickGroup = None					
					#print "Done. \n" # Legibility.

				elif LineSections[0] == "OfflineMessage":
					# Format is: OfflineMessage=<Sender's Group's MasterNickname>,<Dest nick>,<Message>,<Timestamp>
					Params = LineSections[1].split(',')
					for i in range(len(Params)):
						Params[i] = Params[i].strip('\n').strip('"')
					
					if len(Params) != 4:
						print "Bad OfflineMessage entry, skipping!"
						print LineSections[1]
						continue
					
					#print "Loading OfflineMessage from: " + Params[0]					
					NewOfflineMessage = OfflineMessage(self.GetGroupOfNickname(Params[0]), Params[1], Params[2])
					NewOfflineMessage.TimeSent = datetime.strptime(Params[3], TIMESTAMP_FORMAT) 

					self.OfflineMessageList.AddMessage(NewOfflineMessage)
					#print "Done. \n"

				elif LineSections[0] == "AccessGroup":
					# Format is: "AccessGroup=<Group Name>,<Nick group MasterNickname 0>,<Nick group MasterNickname N> 

					Params = LineSections[1].split(',')
					for i in range(len(Params)):
						Params[i] = Params[i].strip('\n').strip('"')

					if len(Params) < 2:
						print "Bad AccessGroup entry, skipping!"					
						print LineSections[1]
						continue

					print "Creating an access group: " + Params[0]
					ActuallyCreateGroup = True

					for Group in self.Groups:
						if Params[0] == Group.GroupName:
							ActuallyCreateGroup = False
							
					if ActuallyCreateGroup:					
						NewAccessGroup = IRCAccessGroup(Params[0])

						for i in range(1, len(Params)):
							#print "Adding nickgroup of " + Params[i] + " to it..."
							NewAccessGroup.AddNickGroup(self.GetGroupOfNickname(Params[i]))						
										
						self.Groups.append(NewAccessGroup)
					#else:
						#print "Group was already in the list"

					#print "Done. \n"
				#elif LineSections[0] == "CommandGroup": ...
			except:
				print "Something went epicly wrong during parsing the state file!"
				print "Line:"
				print Line
				print "Attempting to continue..."
				continue

		print "Done parsing state file!\n" # Extra whitespace for legibility

	def __init__(self, NickServPass):
		# Much one time initialisation to default-default values.
		# Then try to get state file info.
		self.ZTL = 1
		self.NerfSocial = "No one has set this yet!"
		self.PubSocial = "No one has set this yet!"
		self.LogFile = None
		self.OfflineMessageList = OfflineMessageList()
		self.Nickgroups = []
		self.NewestNickGroup = None
		self.Groups = [] # Of IRCAccessGroups
		self.CommandList = dict()

		# Setup some of the defaults:
		# Need to create the two special groups, ADMINS and FLAT_MEMBERS
		# Ensure we know who these people are:		
		for Nicknames in ADMINS:
			Grp = self.GetGroupOfNickname(Nicknames[0])			
			print "Created nick group for " + Nicknames[0]
			for Nick in Nicknames:
				print "Added " + Nick + " to that group"				
				Grp.AddNickname(Nick) # Duplicates are prevented by this routine

		print ""

		for Nicknames in FLAT_MEMBERS:
			Grp = self.GetGroupOfNickname(Nicknames[0])			
			for Nick in Nicknames:
				Grp.AddNickname(Nick)

		# Now make the two IRCAccessGroups:
		AdminGrp = IRCAccessGroup("ADMINS")
		for Nicknames in ADMINS:
			AdminGrp.AddNickGroup(self.GetGroupOfNickname(Nicknames[0]))

		self.Groups.append(AdminGrp)

		FlatMembersGrp = IRCAccessGroup("FLAT_MEMBERS")
		for Nicknames in FLAT_MEMBERS:
			FlatMembersGrp.AddNickGroup(self.GetGroupOfNickname(Nicknames[0]))		

		self.Groups.append(FlatMembersGrp)

		# Have to fill up CommandList to contain
		# dict's containing all the fields of a command.
		# This way, dispatch is through hashing of text, and binary search.
		ANYONE = CMDAccessGroup() # An empty group => anyone can use it

		for DefaultCmd in ShaunBot.DEFAULT_COMMANDS:
			NewCmdContainer = dict()
			NewCmdContainer[CMD_CMD] = DefaultCmd[CMD_CMD] # Cmd's name
			NewCmdContainer[CMD_FUNC] = DefaultCmd[CMD_FUNC]
			NewCmdContainer[CMD_USAGE] = DefaultCmd[CMD_USAGE]
			NewCmdContainer[CMD_HELP_TEXT] = DefaultCmd[CMD_HELP_TEXT]
			if len(DefaultCmd[CMD_GROUPS]) == 0:
				NewCmdContainer[CMD_GROUPS] = ANYONE
			else:			
				NewCmdContainer[CMD_GROUPS] = CMDAccessGroup()
				for GroupName in DefaultCmd[CMD_GROUPS]:			
					NewCmdContainer[CMD_GROUPS].AddAccessGroup(self.GetAccessGroup(GroupName))

			# Now add the NewCmdContainer into self.CommandList:
			self.CommandList[NewCmdContainer[CMD_CMD]] = NewCmdContainer
		
		self.Bot = None	

		# Also, now set the NickServPass:
		global NICKSERV_PASS
		NICKSERV_PASS = NickServPass	

		self.ReadStateFile()

	def OnPrivMsg(self, Sender, ReplyTo, Headers, Message):
		self.Log(Sender, ReplyTo, Message) 
		
		if Message.startswith('!'):
			# Try to see if it is a command:
			Words = Message.split(' ')
			Cmd = self.CommandList.get(Words[0])
			
			# there are some commands (eg: Nerfsocial) that are different functions
			# based on whether or not there was a space.
			# Then there are commands like quit which is the same function, but with optional args, based on whether there was a space.
			if len(Words) != 1:
				# Might be an alternative command/form:
				AltCmd = self.CommandList.get(Words[0] + ' ')
				if (AltCmd != None) and (AltCmd != Cmd):
					Cmd = AltCmd # There was a second, different function that should be called instead.			

			if Cmd != None:
				# Was a command, is Sender permitted to use it?
				if Cmd[CMD_GROUPS].AllowAnyone():
					Cmd[CMD_FUNC](self, Sender, ReplyTo, Headers, Message, Cmd)
				else:
					# Sender must be in the commands access group:
					if Sender in Cmd[CMD_GROUPS]:
						# Sender must also be auth'd with nickserv:
						self.Bot.identify(Sender, OnCmdAuthSuccess, [self, Sender, ReplyTo, Headers, Message, Cmd], OnAuthFailure, [])
						# Command execution is now async, due to network request. all done.
				

	def OnJoin(self, Sender, Headers, Message):
		Grp = self.GetGroupOfNickname(Sender)
		if Grp == self.NewestNickGroup:
			# This is the first time we have met this person:
			self.Say([CHANNEL], "Hello " + Sender + "! Welcome to #BUZAN, the IRC channel for Bristol's own Zombie defence society! Type !help for help")
			self.NewestNickGroup = None

		# Deliver message(s), if any:		
		Messages = self.OfflineMessageList.CheckForMessages(Grp)
		for Msg in Messages:
			self.Say([Msg.Dest], str(Msg))

	def LagHandler(self):
		global NICKSERV_PASS		
		# Due to network latency, best to wait for
		# numeric "376" (end of MOTD) before trying to join and ID with NickServ	
		self.Bot.join(CHANNEL)
		self.Bot.say("NICKSERV", "identify " + NICKSERV_PASS)

	# Main bot function:
	def Run(self):
		global BINDINGS
	
		self.Bot = ircBot(NETWORK, PORT, NICKNAME, DESCRIPTION)
		for Binding in BINDINGS:
			self.Bot.bind(Binding[0], Binding[1])
    
		self.Bot.connect()
		# Joining and IDing with NickServ handled in LagHandler
		self.Bot.run()

		self.WriteStateFile()

		if self.RestartSelf:
			print "Restarting self..."
			subprocess.Popen(COMMAND_FOR_SELF, shell = True)
		

#############################################
# Backup thread:
def OnBackup():
	global ShaunBotInst
	
	# Todo: make things expire.
	ShaunBotInst.WriteStateFile()

global BackupThread
BackupThread = threading.Timer(BACKUP_INTERVAL, OnBackup)
	
#############################################
# PUT IRC BINDINGS HERE
def OnPrivMsg(Bot, Sender, Headers, Message):
	global ShaunBotInst
		
	ReplyTo = Sender
	# ... unless there is a channel inside Headers, in which case:
	for s in Headers:
		if s.startswith('#'):
			ReplyTo = s	
			break

	ShaunBotInst.OnPrivMsg(Sender, ReplyTo, Headers, Message)

def OnJoin(Bot, Sender, Headers, Message):
	global ShaunBotInst
	
	ShaunBotInst.OnJoin(Sender, Headers, Message)

def LagHandler(Bot, Sender, Headers, Message):
	global ShaunBotInst

	ShaunBotInst.LagHandler()	

global BINDINGS

BINDINGS = [
	["PRIVMSG", OnPrivMsg],
	["JOIN", OnJoin],
	["376", LagHandler]]

# Main program:
print "Welcome to ShaunBot - ZomPoc Tracker..."

if len(argv) < 2:
	print "Must supply NickServ Password on the command line for security reasons!"
	exit(-1)

global ShaunBotInst
global BackupThread

ShaunBotInst = ShaunBot(argv[1]) # Nickserv pass

BackupThread.start()

ShaunBotInst.Run()

BackupThread = None

print "Quitting sanely...\n"
