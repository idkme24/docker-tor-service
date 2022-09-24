#!/usr/bin/env python3

import os
import sys
import json
import time
import yaml
import subprocess

#########################################################
#                                                       #
#       Tor Container Service Setup Script              #
#       Peyton Rathbun - 9/24/2022                      #
#                                                       #
#########################################################
#
#   Environment variables used by the script to configure
#   the Tor configuration file.
#
#   ENV                     DETAIL
#--------------------------------------------------------
#   PUID                    uid of user
#   PGID                    gid of user
#   ROLE                    function of tor service 'service,relay,proxy'
#   YAML_CFG                use torsrv.yml configuration file
#   ONIONSERVICE_NAME       name of hiddenservice
#   ONIONSERVICE_DIR        hiddenservice directory
#   ONIONSERVICE_PORT       hiddenservice virtual port
#   ONIONSERVICE_HOST       hiddenservice IP:PORT of service
#   PROXY_PORT              proxy service port
#   PROXY_ADDRESS           bind proxy service to address
#   PROXY_ACCEPT            subnets which to accept SOCKS connections
#   PROXY_REJECT            subnets which NOT to accept SOCKS connections
#   CONTROL_PORT
#   CONTROL_PASSWORD
#   CONTROL_COOKIE
#   CFG_OVERWRITE           overwrite old cfg
#   CFG_PATH                path to cfg in container
#   BASE_DIR                base path for tor config/services

class TorService():
    def __init__(self, role, usecfg):
        ## Define Defaults Variables
        self.torservice_uid = os.popen("/usr/bin/getent passwd torservice | /usr/bin/awk -F':' '{print $3}'").read()
        self.torservice_gid = os.popen("/usr/bin/getent passwd torservice | /usr/bin/awk -F':' '{print $4}'").read()
        self.valid_roles = ['service','proxy','relay','control']
        self.confpath = '/tor/torrc'
        self.ymlcfg = '/tor/torsrv.yml'
        self.torbase = '/tor'
        self.tor_role = role
        self.tor_yaml_cfg = usecfg
        self.services = {}
        self.configdata = []
        self.torconfiguration = {"cfg": {}}

        ## If both ENV Vars and a CFG are passed default to cfg
        if (self.tor_role in self.valid_roles and bool(self.tor_yaml_cfg) == True):
            print('INFO: Defaulting to YAML_CFG. Ignoring other ENVs')

        ## Check for valid service role
        if (self.tor_role not in self.valid_roles and bool(self.tor_yaml_cfg) == False):
            print('ERROR: Requires a role "service, proxy, relay"')
            sys.exit(1)

        ## Update tor base dir
        try:
            torbaseenv = os.environ['BASE_DIR']
            if (torbaseenv != ''):
                self.torbase = torbaseenv
                print('INFO: Setting BASE_DIR to: '+str(self.torbase))
        except:
            pass
        self.torconfiguration['cfg']['BaseDir'] = self.torbase

        ## Update torrc file path
        try:
            confpathenv = os.environ['CFG_PATH']
            if (confpathenv != ''):
                self.confpath = confpathenv
        except:
            if (self.torbase != '/tor'):
                self.confpath = str(self.torbase+'/torrc')
                self.ymlcfg = str(self.torbase+'/torsrv.yml')
            pass
        self.torconfiguration['cfg']['CFGPath'] = self.confpath

        ## Load torsrv.yml file if applicable
        if (bool(self.tor_yaml_cfg) == True):
            with open(self.ymlcfg,'r') as tscfg:
                self.torconfiguration.update(yaml.safe_load(tscfg))

            self.tor_role = list(self.torconfiguration['torsrv'].keys())[0]

            self.torconfiguration['cfg']['Role'] = self.tor_role
            self.torconfiguration['cfg']['UseYAMLCFG'] = True
        else:
            self.torconfiguration['torsrv'] = {}

        ## Load Applicable ENVs if not using YAML_CFG
        if (bool(self.tor_yaml_cfg) == False):
            self.torconfiguration['cfg']['UseYAMLCFG'] = False
            self.torconfiguration['cfg']['Role'] = self.tor_role
            ## Onion Service
            if (self.tor_role == 'service'):
                try:
                    self.torconfiguration['torsrv']['service'] = {os.environ['ONIONSERVICE_NAME']: {}}
                    Oservice = self.torconfiguration['torsrv']['service'][os.environ['ONIONSERVICE_NAME']]
                    Oservice['Dir'] = os.environ['ONIONSERVICE_DIR']
                    Oservice['Vport'] = os.environ['ONIONSERVICE_PORT']
                    Oservice['Host'] = os.environ['ONIONSERVICE_HOST']
                    Oservice['Name'] = os.environ['ONIONSERVICE_NAME']
                except Exception as ENVerr:
                    print('ERROR: environment variable TOR_HS not set')
                    print(ENVerr)
                    sys.exit(1)

            ## Proxy Service
            elif (self.tor_role == 'proxy'):
                try:
                    self.torconfiguration['torsrv']['proxy'] = {}
                    OProxy = self.torconfiguration['torsrv']['proxy']
                    OProxy['Port'] = os.environ['PROXY_PORT']
                    try:
                        OProxy['Address'] = os.environ['PROXY_ADDRESS']
                    except:
                        pass
                    OProxy['Accept'] = os.environ['PROXY_ACCEPT']
                    try:
                        OProxy['Reject'] = os.environ['PROXY_REJECT']
                    except:
                        pass
                except:
                    print('ERROR: environment variable TOR_PROXY not set')
                    sys.exit(1)

            ## Control Service
            elif (self.tor_role == 'control'):
                try:
                    self.torconfiguration['torsrv']['control'] = {}
                    OControl = self.torconfiguration['torsrv']['control']
                    OControl['Port'] = os.environ['CONTROL_PORT']
                    try:
                        OControl['Password'] = os.environ['CONTROL_PASSWORD']
                    except:
                        pass

                    try:
                        OControl['Cookie'] = os.environ['CONTROL_COOKIE']
                    except:
                        pass
                except:
                    print('ERROR: environment variable TOR_PROXY not set')
                    sys.exit(1)

            ## Relay Service
            elif (self.tor_role == 'relay'):
                print('WIP')

        if (self.tor_role == 'service'):
            self.HiddenService()
        elif (self.tor_role == 'proxy'):
            self.TorProxy()
        elif (self.tor_role == 'control'):
            self.TorControl()
        elif (self.tor_role == 'relay'):
            print('WIP')

        ## Configuration Files/directories
        self.TorConfiguration()


        print('INFO: entrypoint.py and torrc configurations')
        print(json.dumps(self.torconfiguration, indent=4))
        print()
        for Line in self.configdata:
            print(Line)

    def WriteTorrcFile(self):
        print('INFO: Writing Configuration file to '+str(self.confpath))
        fh_torrc = open(self.confpath, 'w')
        for Line in self.configdata:
            fh_torrc.write(Line+'\n')
        fh_torrc.close()

    def TorConfiguration(self):
        ## create directories if applicable
        if (os.path.exists(self.torbase)):
            print('INFO: Tor Base Directory Exists')
        else:
            print('INFO: Creating Tor Base Directory')
            os.mkdir(self.torbase,0o700)

        if (self.tor_role == 'service'):
            for Service in self.torconfiguration['torsrv']['service']:
                Dir = self.torconfiguration['torsrv']['service'][Service]['Dir']
                if (os.path.exists(Dir)):
                    print('INFO: service path '+str(Dir)+' allready exists')
                else:
                    print('INFO: creating service path '+str(Dir))
                    os.mkdir(Dir,0o700)

        ## Check for existing torrc file
        if (os.path.exists(self.confpath)):
            print('INFO: torrc file present')
            try:
                os.environ['CFG_OVERWRITE']
                AllowOverWrite = True
                print('INFO: Allow configuration file to be overwritten')
            except:
                AllowOverWrite = False

            try:
                if (bool(AllowOverWrite) == True):
                    self.WriteTorrcFile()
                else:
                    print('INFO: Will NOT overwrite Configuration file')
            except:
                print('ERROR: Could not write Configuration file')
                pass
        else:
            print('INFO: torrrc file missing will create one')
            self.WriteTorrcFile()

        ## update uid/gid of torservice
        try:
            self.torservice_uid = os.environ['PUID']
            os.popen('/usr/bin/usermod -o -u '+str(self.torservice_uid)+' torservice')
            print('INFO: Updating toerservice uid to: '+str(self.torservice_uid))
        except:
            print('INFO: Using default toerservice uid')
            pass

        try:
            self.torservice_gid = os.environ['PGID']
            os.popen('/usr/bin/groupmod -o -g '+str(self.torservice_gid)+' torservice')
            print('INFO: Updating toerservice gid to: '+str(self.torservice_gid))
        except:
            print('INFO: Using default toerservice gid')
            pass

        ## update directory/file permissions
        print('INFO: Updating user, group, and file permissions')
        os.popen('/usr/bin/chown -R torservice:torservice '+str(self.torbase))

    def TorProxy(self):
        self.configdata.append('#### Tor Proxy Configuration ####')
        Proxy = self.torconfiguration['torsrv']['proxy']

        try:
            Address = Proxy['Address']
            Port = Proxy['Port']
            SocketString = "SocksPort "+str(Address)+':'+str(Port)
        except:
            Port = Proxy['Port']
            SocketString = "SocksPort "+str(Port)

        self.configdata.append(SocketString)
        self.configdata.append(str("SocksPolicy accept "+str(Proxy['Accept'])))

        try:
            self.configdata.append(str("SocksPolicy reject "+str(Proxy['Reject'])))
        except:
            pass


    def TorControl(self):
        self.configdata.append('#### Tor Controler Configuration ####')
        Control = self.torconfiguration['torsrv']['control']

        self.configdata.append(str('ControlPort '+Control['Port']))

        AuthMethodSet = False

        try:
            HashedPW = os.popen("tor --hash-password "+str(Control['Password']))
            self.configdata.append(str('HashedControlPassword '+HashedPW))
            AuthMethodSet = True
        except:
            pass

        try:
            self.configdata.append(str('CookieAuthentication '+Control['Cookie']))
            AuthMethodSet = True
        except:
            pass

        if (bool(AuthMethodSet) == False):
            self.configdata.append(str('CookieAuthentication 1'))


    def HiddenService(self):
        self.configdata.append('#### Tor HiddenService Configuration ####')
        Service = self.torconfiguration['torsrv']['service']


        for ServiceName in Service:
            self.configdata.append('\n## HiddenService '+str(ServiceName))

            HSSir = 'HiddenServiceDir '+str(Service[ServiceName]['Dir'])
            self.configdata.append(HSSir)
            if (bool(self.tor_yaml_cfg) == False):
                HSPort = 'HiddenServicePort '+str(Service[ServiceName]['Vport'])+' '+str(Service[ServiceName]['Host'])
                self.configdata.append(HSPort)
            else:
                print(json.dumps(Service[ServiceName]['Vports'], indent=4))
                for Vport in Service[ServiceName]['Vports']:
                    Host = Service[ServiceName]['Vports'][Vport]
                    HSPort = 'HiddenServicePort '+str(Vport)+' '+str(Host)
                    self.configdata.append(HSPort)

            self.configdata.append('\n')

def main():
    try:
        usecfg = os.environ['YAML_CFG']
    except:
        usecfg = False

    try:
        role = os.environ['ROLE']
    except:
        if (bool(usecfg) == False):
            print('ERROR: environment variable ROLE not set')
            sys.exit(1)
        else:
            role = ''

    InitTorService = TorService(role,usecfg)

if (__name__ == "__main__"):
    main()
