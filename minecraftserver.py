import subprocess
import time
import sys
import threading

class mcserver:
	def __getinitargs__(self):
		# We need to call the constructor on unpickling:
		return [self.SaveInterval, self.ServerDir, self.ServerCmd, self.SavingCmd]

	def __getstate__(self):
		# Do not return ANYTHING
		return []

	def __setstate__(self, State):
		# State is the same as the result of __getstate__()
		# ie: is empty:
		if len(State) != 0:
			raise "Incompatable state! Expected an empty tuple!"

	def __OnTimer(self):
		# Exists so that changing it is easier.
		self.ManualSave()
		
	def __init__(self, SaveInterval, ServerDir, ServerCmd, SavingCmd):
		""" Encapsulates an instance of a minecraft server, automatically
			saving the level every SaveInterval seconds, running SavingCmd,
			which is normally a backing up command. (eg: cp -u ...)
			
			ServerCmd must be the full command for the server (ie: not relative to ServerDir,
			which is used to ensure the Minecraft server's files end up in the right directory. """
			
		self.SaveInterval = SaveInterval
		if ServerDir.endswith('/'): # Must not have trailing /
			ServerDir = ServerDir[:len(ServerDir) - 1]
		
		self.ServerDir = ServerDir		
		self.ServerCmd = ServerCmd
		self.SavingCmd = SavingCmd
		self.MinecraftServer = None
		self.Lock = threading.Lock()
		self.TimingThread = threading.Timer(SaveInterval, self.__OnTimer, [])

	def __IssueCommand(self, Command):
		# a macro round server.stdin.write(Command with enforced '\n')
		# Does not use the lock so it can be combined in various wonderful ways:
		# Do not call this directly

		if self.MinecraftServer != None:
			if not Command.endswith('\n'):
				Command += '\n'
			
			self.MinecraftServer.stdin.write(Command)			
	
	def Start(self):
		if self.MinecraftServer == None:
			with self.Lock:				
				self.MinecraftServer = subprocess.Popen(self.ServerCmd, shell = True, stdin = subprocess.PIPE, cwd = self.ServerDir)
				self.TimingThread.start()			
		
		# Otherwise, we created it successfully, or this is a no-op (already started)
		return True

	def Stop(self):
		if self.MinecraftServer != None:			
			with self.Lock:				
				# Must be done inside of the lock
				self.__IssueCommand('stop')
				# This does somewhat presuppose the server hasn't crashed...
				Ret = self.MinecraftServer.wait()
				self.MinecraftServer = None

				return (Ret == 0)
			
		
		return True # No-op (already stopped)
	
	def Running(self):
		if self.MinecraftServer == None:
			return False
		else:
			return True

	def IssueCommand(self, Cmds):
		""" Issues the command(s) Cmds to the MC server.
			Note that each cmd does not have to end with <newline>, this is enforced. 
			No validation is done on server commands right now. """
				
		with self.Lock:
			try:
				for s in Cmds:
					__IssueCommand(s)
			except:
				return False
			
		return True
	
	def ManualSave(self):
		""" Disables auto-saving, forces a level wide save,
			backs up the files (using self.SavingCmd), re-enables auto-saving. """
		self.__IssueCommand('save-off')
		self.__IssueCommand('save-all')
		
		# May be a delay between us issuing the command, and server running it:
		# so wait for 5 seconds:
		time.sleep(5)

		# Now try to backup:		
		BackingUp = subprocess.Popen(self.SavingCmd, shell = True)
		Ret = BackingUp.wait()
		
		self.__IssueCommand('save-on')

		return (Ret == 0)

	# Convenience functions:
	def Restart(self):
		""" Restarts the server, if it is running """
		if self.Running():
			Result = self.Stop()
			if Result:
				Result = self.Start()
			
			return Result
		else:
			return True # no-op
