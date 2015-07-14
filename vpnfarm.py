#!/usr/bin/python

## VPN Farm script for both the server and its clients
#    Without indicating a mode, it should start the daemon and get it ready

## ATTENTION:
# Our VPN client uses openvpn. This should be changed in case of a different VPN 'engine':

import datetime, json, pty, os, subprocess, sys, time

#### Global variables

# This channel list works as follows:
#   Each clients stores a list of "Service - Port" at the server after connecting
#     It also cleans up old items
#   The server reads that list and makes sure the ports are open (if the client is still there)

channel_list_folder = '/home/vpnfarm'
channel_list_template = 'channelsjson'
channel_list = channel_list_folder + '/' + channel_list_template

#server_url = 'fonseca.de.com'
server_url = '85.214.251.58'

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
    elif mode == 'restart':
      self.do_stop()
      self.do_check_and_connect()

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

  def do_read_services(self):
    self.portchannels = {}
    channel_localport = 8040 
    allfiles = [ f for f in os.listdir(channel_list_folder) if os.path.isfile(os.path.join(channel_list_folder,f)) ]
    for filename in allfiles:
      if channel_list_template in filename:
        with open(channel_list_folder + '/' + filename) as data_file:    
          data = json.load(data_file)
          channel_ip = filename.replace(channel_list_template,'').replace('_','')
          if (channel_ip != ''): 
            for entry in data["channels"]:
              channel_remote = channel_ip + ':' + entry + ':' + data["channels"][entry]
              channel_localport += 1
              self.portchannels[channel_localport] = channel_remote
 
  def do_connect_services(self):
    self.do_read_services()
    ##TODO: load default ifconfig, then open one after the other.
    ##      SINCE it does not seem to work from here, I'll just inform the user 
    ##    (yes, I know this is cheap)
    print('ATTENTION: You\'ll have to open the related ports! Copy and paste the following:i\n')
    print('/sbin/iptables-restore < /root/vpnfarm/iptables_base')
    for port in self.portchannels:
      dest_ip = self.portchannels[port].split(':')[0]
      dest_port = self.portchannels[port].split(':')[2]
      print('iptables -t nat -A PREROUTING -p tcp -d ' + server_url + ' --dport ' + str(port) + ' -j DNAT --to-destination ' + dest_ip + ':' + dest_port)


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
    elif mode == 'restart':
      self.do_stop()
      self.do_check_and_connect()

## Actions to take ##

  def do_check_and_connect(self):
    self.pid = self.get_pid()
    if self.pid == "":
      self.do_start()
      start_pid = self.get_pid()   
      if start_pid != "":
        print_ts('The VPN Client was not running! The new PID is ' + start_pid)
        # We need to wait a second or two, to let everything get configured
        time.sleep(3)
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
      #stop_command = subprocess.Popen('kill ' + self.pid + ' && sleep 2s',
      stop_command = subprocess.Popen('kill ' + self.pid ,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      stop_result, stop_err = stop_command.communicate()
      time.sleep(2)
      stop_pid = self.get_pid()   
      if stop_pid == '':
        print_ts('The VPN Client has been stopped!')
      else:
        print_ts('Something weird happened, the VPN Client has been stopped but some processes are still running. PLEASE CHECK!')
        print_ts(stop_pid + '<- see? this is the PID')
      return

  def do_register_services(self):
    vpn_client_ip = self.get_vpnclient_ip()
    command = 'scp -i /home/vpnfarm/.ssh/id_rsa ' + channel_list + ' vpnfarm@' + server_url + ':' + channel_list + '_' + vpn_client_ip
    copy2server_command = subprocess.Popen(command,
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    copy2server, copy2server_err = copy2server_command.communicate()
    
    
## Information to get ##

  def get_pid(self):
    pid_command = subprocess.Popen("ps aux | grep 'openvpn ' | grep -v grep | awk '{print $2}'",
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid, pid_err = pid_command.communicate()
    return pid.rstrip()

  def get_vpnclient_ip(self):
    vpnip_command = subprocess.Popen("ifconfig tun0 | grep ' addr:'",
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vpnip_result, vpnip_err = vpnip_command.communicate()
    # Not using re.split here, to avoid format issues 
    vpnip = vpnip_result.split()[1].split(':')[1]
    return vpnip



####       MAIN

def show_error():
  print('SYNTAX ERROR! ')
  print(sys.argv[0] + ' [server|client] <mode>')
  print('        , where mode can be')
  print('        1.- for the SERVER machine:')
  print('          - <nothing> also known as auto-mode. The server gets everything ready for the clients that are connected.')
  print('          - list      show a list (JSON) of all clients connected.')
  print('          - stop      the server gets stopped if it\'s running.')
  print('          - restart   the server gets stopped, then up and running again.')
  print('        2.- for the CLIENT machine:')
  print('          - <nothing> again, auto-mode. The client makes himself available to the openvpn server.')
  print('          - stop      the client gets stopped if it\'s running.')
  print('          - restart   the client gets stopped, then up and running again.')

def print_ts(message):
  ts = str(datetime.datetime.now()).split('.')[0]
  print(ts + ' - ' + message)

def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output

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
