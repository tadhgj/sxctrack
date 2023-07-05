import os
# move oneStep.py to oneStepOld.py. force overwrite. Old copies will be available in github anyways
os.rename("oneStep.py", "oneStepOld.py")

# curl oneStep.py from github
try:
    os.system("curl https://raw.githubusercontent.com/tadhgj/sxctrack/main/oneStep.py > oneStep.py")
    # if success, good
    print("Successfully curled oneStep.py from github")
    exit()
except:
    # if fail, move oneStepOld.py back to oneStep.py
    print("Failed to curl oneStep.py from github")
    os.rename("oneStepOld.py", "oneStep.py")
    exit()
