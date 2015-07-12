#!/usr/bin/python

## VPN Farm script for both the server and its clients
#    Without parameters, it should give back the following:
#    VPN UP/DOWN
#    client1 IP1 oldIP1

import datetime, json, pty, os, subprocess, sys

#### Global variables

# This channel list works as follows:
#   Each clients stores a list of "Service - Port" at the server after connecting
#     It also cleans up old items
#   The server reads that list and makes sure the ports are open (if the client is still there)
channel_list = '/home/vpnfarm/channels.json'


####  SERVER  ####
##################

class FarmServer(object):
  def __init__(self,mode):
    # Default: check that everything is working fine
    if mode == '':
      self.do_check_and_connect()
    elif mode == 'list':
      self.get_connectedclients()
    elif mode == 'stop':
      self.do_stop()

## Actions to take ##

  def do_check_and_connect(self):
    self.pid = self.get_pid()
    if self.pid == "":
      self.do_start()
      start_pid = self.get_pid()
      if start_pid != "":
        print_ts('The VPN Server was not running! The new PID is ' + start_pid)
        self.do_connect_services()
        return
      else:
        print_ts('ERROR! The VPN Server was not running, AND it could not be started either!')
        return


  def do_start(self):
    start_command = subprocess.Popen('/etc/init.d/openvpnas start',
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    start_result, start_err = start_command.communicate()

  def do_stop(self):
    self.pid = self.get_pid()
    if self.pid == "":
      print_ts('The VPN Server was not running! (nothing had to be stopped)')
      return
    else:
      start_command = subprocess.Popen('/etc/init.d/openvpnas stop',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      start_result, start_err = start_command.communicate() 
      start_pid = self.get_pid()   
      if start_pid == '':
        print_ts('The VPN Server has been stopped!')
      else:
        print_ts('Something weird happened, the VPN Server has been stopped but some processes are still running. PLEASE CHECK!')
      return

  def do_connect_services(self):
    with open(channel_list) as data_file:    
      data = json.load(data_file)
    print(data["clients"])
    

## Information to get ##

  def get_pid(self):
    # Our VPN server uses openvpn access server. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen('AUXPID=$(cat /var/run/openvpnas.pid); if [ "$(ps aux | grep $AUXPID | grep -v grep)" != "" ]; then echo $AUXPID; fi', 
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()    
    return pid.rstrip()

  def get_status(self):
    status_process = subprocess.Popen("/usr/local/openvpn_as/scripts/sacli VPNStatus", shell=True,
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
    status_out, status_err = status_process.communicate()
    return json.loads(status_out)

  def get_connectedclients(self):
    current_status = self.get_status()
    for entry in current_status:
      client = current_status[entry]["client_list"]
      if client:
        print client

####  CLIENT  ####
##################

class FarmClient(object):
  def __init__(self,mode):
    # Default: check that everything is working fine
    if mode == '':
      self.do_check_and_connect()
    elif mode == 'stop':
      self.do_stop()

## Actions to take ##

  def do_check_and_connect(self):
    self.pid = self.get_pid()
    if self.pid == "":
      self.do_start()
      start_pid = self.get_pid()   
      if start_pid != "":
        print_ts('The VPN Client was not running! The new PID is ' + start_pid)
        self.do_register_services()
        return
      else:
        print_ts('ERROR! The VPN Client was not running, AND it could not be started either!')
        return

  def do_start(self):
    master, slave = pty.openpty()
    start_command = subprocess.Popen('/usr/sbin/openvpn /etc/openvpn/client_vpnfarm.ovpn > /etc/openvpn/openvpn.log &',
                           shell=True, stdout=slave, stderr=slave, close_fds=True)
    result = os.fdopen(master)

  def do_stop(self):
    self.pid = self.get_pid()
    if self.pid == "":
      print_ts('The VPN Client was not running! (nothing had to be stopped)')
      return
    else:
      stop_command = subprocess.Popen('kill ' + self.pid + ' && sleep 2s',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      stop_result, stop_err = stop_command.communicate() 
      stop_pid = self.get_pid()   
      if stop_pid == '':
        print_ts('The VPN Client has been stopped!')
      else:
        print_ts('Something weird happened, the VPN Client has been stopped but some processes are still running. PLEASE CHECK!')
        print_ts(stop_pid + '<- see? this is the PID')
      return

  def do_register_services(self):
    pass
    
    
## Information to get ##

  def get_pid(self):
    # Our VPN client uses openvpn. This should be changed in case of a different VPN 'engine':
    pid_command = subprocess.Popen("ps aux | grep 'openvpn ' | grep -v grep | awk '{print $2}'",
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    pid, err = pid_command.communicate()
    return pid.rstrip()



####       MAIN

def show_error():
  print('SYNTAX ERROR! ')
  print(sys.argv[0] + ' [server|client] <mode>')
  print('        , where mode can be')
  print('        1.- for the SERVER machine:')
  print('          - <nothing>, also known as auto-mode. The server gets everything ready for the clients that are connected.')
  print('          - list, show a list (JSON) of all clients connected.')
  print('          - stop, the server gets stopped if it\'s running.')
  print('        2.- for the CLIENT machine:')
  print('          - <nothing>, again, auto-mode. The client makes himself available to the openvpn server.')
  print('          - stop, the client gets stopped if it\'s running.')

def print_ts(message):
  ts = str(datetime.datetime.now()).split('.')[0]
  print(ts + ' - ' + message)


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
