#!/usr/bin/python

## VPN Farm script for both the server and its clients
#    Without parameters, it should give back the following:
#    VPN UP/DOWN
#    client1 IP1 oldIP1

import json, subprocess, sys

class VPNStatus(object):
  def __init__(self):
    process = subprocess.Popen("/usr/local/openvpn_as/scripts/sacli VPNStatus", shell=True,
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    out, err = process.communicate()
    self.result = json.loads(out)

  def show_clients(self):
    for entry in self.result:
      client = self.result[entry]["client_list"]
      if client:
        print client


class FarmServer(object):
  def __init__(self):
    self.pid = self.get_pid()
    if self.pid == "":
      print "The VPN Server is not running! Please start the service first."
      return
    else:
      print("the pid is "+ self.pid)

  def get_pid(self):
    # Our VPN server uses openvpn access server. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen('AUXPID=$(cat /var/run/openvpnas.pid); if [ "$(ps aux | grep $AUXPID | grep -v grep)" != "" ]; then echo $AUXPID; fi', 
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()    
    return pid.rstrip()

class FarmClient(object):
  def __init__(self):
    self.pid = self.get_pid()
    if self.pid == "":
      print "The VPN Client is not running! Please start the service first."
      return
    else:
      print("the pid is "+ self.pid)

  # TODO: this gets more than one result? check it!
  def get_pid(self):
    # Our VPN client uses openvpn. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen("ps aux | grep openvpn | grep -v grep | awk '{print $2}'",
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()
    return pid.rstrip()



def show_error():
  print('SYNTAX ERROR! ')
  print(sys.argv[0] + ' [server|client]')

if __name__ == '__main__':
  try:
    mode = sys.argv[1]
    if (mode == 'server'):
      instance = FarmServer() 
    elif (mode == 'client'):
      instance = FarmClient()
    else:
      show_error()
  except(IndexError):
   show_error()
  #current_status = VPNStatus()

  #current_status.show_clients()
