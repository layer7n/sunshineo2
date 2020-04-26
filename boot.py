import asyncio
import sunshineo2
import sys

try:
	arg = sys.argv[1]
	if(arg == "-l"):
		sunshineo2 = sunshineo2.o2(type="login")
	elif(arg == "-g"):
		sunshineo2 = sunshineo2.o2(type="game")

except IndexError:
	print()
	print("usage: boot.py [-l] [-g]")
	print()
	print("arguments:")
	print(" -l\t\tStart 'sunshineo2' login server instance.")
	print(" -g\t\tStart 'sunshineo2' game  server instance.")
	print()
	sys.exit()


try:
	asyncio.run(sunshineo2.serverLoop())
	
except (KeyboardInterrupt):
	print("\nExit\n")
	sys.exit()