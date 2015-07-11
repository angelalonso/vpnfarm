#!/usr/bin/python

## VPN Farm script for both the server and its clients
#    Without parameters, it should give back the following:
#    VPN UP/DOWN
#    client1 IP1 oldIP1

import json, pty, os, subprocess, sys

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
  def __init__(self,mode):
    # Default: check that everything is working fine
    if mode == '':
      self.do_check_and_connect()
    elif mode == 'stop':
      self.do_stop()

  def do_check_and_connect(self):
    self.pid = self.get_pid()
    if self.pid == "":
      start_command = subprocess.Popen('/etc/init.d/openvpnas start',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      start_result, start_err = start_command.communicate() 
      start_pid = self.get_pid()   
      print('The VPN Server was not running! The new PID is ' + start_pid)
      return

  def do_stop(self):
    self.pid = self.get_pid()
    if self.pid == "":
      print('The VPN Server was not running! (nothing had to be stopped)')
      return
    else:
      start_command = subprocess.Popen('/etc/init.d/openvpnas stop',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      start_result, start_err = start_command.communicate() 
      start_pid = self.get_pid()   
      if start_pid == '':
        print('The VPN Server has been stopped!')
      else:
        print('Something weird happened, the VPN Server has been stopped but some processes are still running. PLEASE CHECK!')
      return
#####TODO: Add more options


  def get_pid(self):
    # Our VPN server uses openvpn access server. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen('AUXPID=$(cat /var/run/openvpnas.pid); if [ "$(ps aux | grep $AUXPID | grep -v grep)" != "" ]; then echo $AUXPID; fi', 
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()    
    return pid.rstrip()

class FarmClient(object):
  def __init__(self,mode):
#####TODO: Reorder like server
    self.pid = self.get_pid()
    if self.pid == "":
      print "The VPN Client is not running! Please start the service first."
      self.start_newclient()
      print('new pid: ' + self.get_pid())
      #return

  def get_pid(self):
    # Our VPN client uses openvpn. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen("ps aux | grep 'openvpn ' | grep -v grep | awk '{print $2}'",
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()
    return pid.rstrip()

  def start_newclient(self):
    master, slave = pty.openpty()
    start_command = subprocess.Popen('/usr/sbin/openvpn /etc/openvpn/client_vpnfarm.ovpn > /etc/openvpn/openvpn.log &',
                           shell=True, stdout=slave, stderr=slave, close_fds=True)
    result = os.fdopen(master)

def show_error():
  print('SYNTAX ERROR! ')
  print(sys.argv[0] + ' [server|client] <mode>')
  print('        , where mode can be')
  print('        1.- for the SERVER machine:')
  print('          - <nothing>, also known as auto-mode. The server gets everything ready for the clients that are connected.')
  print('          - stop, the server gets stopped if it\'s running.')
  print('        2.- for the CLIENT machine:')
  print('          - <nothing>, again, auto-mode. The client makes himself available to the openvpn server.')

if __name__ == '__main__':
  try:
    machine = sys.argv[1]
    try:
      mode = sys.argv[2] 
    except(IndexError):
      mode = ""
    if (machine == 'server'):
      instance = FarmServer(mode) 
    elif (machine == 'client'):
      instance = FarmClient(mode)
    else:
      show_error()
  except(IndexError):
   show_error()
  #current_status = VPNStatus()

  #current_status.show_clients()
