
import os
import sys
import subprocess


arguments = sys.argv
if (len(arguments) < 2):
    print("Not enough arguments in "+str(arguments))
    sys.exit()
target = arguments[1]
environment = dict(os.environ)
blender = "BLENDER_HOME"
if not (blender in environment):
    print("No \""+blender+"\" in environment")
    sys.exit()
blender = os.path.join(environment[blender], "Blender")
command = [blender, "-b", "-P", os.path.join(os.getcwd(), "blender.py"), "--", target, sys.executable, os.path.join(os.getcwd(), "ombb.py")]
output = subprocess.check_output(command)
print(output.decode())

