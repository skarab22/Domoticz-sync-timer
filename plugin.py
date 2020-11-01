# Python Plugin SyncDeviceToTimer
#
# Created: 01-nov-2020
# Author: Skarab22
# Collaborator: Syrhus
#
"""
<plugin key="SyncDeviceToTimer" name="SyncDeviceToTimer" author="Skarab22" version="1.0.0" externallink="https://github.com/skarab22/Update_timer">
    <params>
	    <param field="Address" label="IP Domoticz" width="250px" required="true"/>
	    <param field="Port" label="Port Domoticz" width="100px" required="true"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import requests
import datetime


now = datetime.datetime.now()

#constants
MON = 1;
TUE = 2;
WED = 4;
THU = 8;
FRI = 16;
SAT = 32;
SUN = 64;
EVERYDAYS = 128;
WEEKDAYS = 256;
WEEKENDS = 512;

SUM_EVERYDAYS = 127;
SUM_WEEKDAYS = 31;
SUM_WEEKENDS = 96;

ONTIME = 2;


class BasePlugin:
    enabled = False

    def url(self, json_cmd):
        return 'http://' + self.HOST + ':'+ self.PORT + json_cmd


    def request(self, json_cmd):
        cmd = self.url(json_cmd)
        Domoticz.Debug(f"url:{cmd}")
        response = requests.get(cmd)
        if response.ok:
            return response.json()

    def get_timer_list(self,ip, port):
        Domoticz.Debug(f"get_timer_list=> {ip}:{port}")
        self.HOST= ip
        self.PORT= port
        
        cmd = '/json.htm?type=schedules&filter=device'
        timers = self.request(cmd)['result']
        Domoticz.Debug(f"timers:{timers}")

        #on filtre les timers actifs
        activeTimers = [timer for timer in timers if timer['Active'] == "true"]

        #print(f"activeTimers:{activeTimers}")

        deviceID = 0
        timer_kvp = {}
        timer_list_id = []
        for timer in activeTimers:
            ID = timer['DeviceRowID']
            timer_list_id.append(ID)
            if deviceID != ID:
                timer_kvp[ID] = []
                deviceID = ID
            
            timer_kvp[ID].append(timer)
            
        #print(f"timer_kvp:{timer_kvp}")
        self.active_day(timer_kvp)
                
    def active_day(self, list_id):
        day = now.weekday()
        for id,timers in list_id.items():
            Domoticz.Debug(f"entre dans la fonction active_timer avec l'ID = {id}")
            triggers = sorted(timers, key=byTime)
            Domoticz.Debug(f"Il y a {len(triggers)} timer pour l'idx {id} ")
            triggers_active_day = []
            
            for j, k in enumerate(triggers):
                Domoticz.Debug(f"Days = {k['Days']}")
                if k['Days'] == EVERYDAYS:
                    Domoticz.Debug('Timer actif tous les jours')
                    bin_active_day = SUM_EVERYDAYS
                elif k['Days'] == WEEKDAYS:
                    Domoticz.Debug('Timer actif jours de semaine')
                    bin_active_day = SUM_WEEKDAYS
                elif k['Days'] == WEEKENDS:
                    Domoticz.Debug('Timer actif le weekend')
                    bin_active_day = SUM_WEEKENDS
                else:
                    bin_active_day = int(k['Days'])
                Domoticz.Debug(f"Nous somme le {day}e jour de la semaine. Valeur Days en binaire = {2**day}")
                if bin_active_day & (2**day) :
                    triggers_active_day.append(k)

            if triggers:
                Domoticz.Debug(f"ID des timer actifs pour ce jours de la semaine : {triggers_active_day}")
                self.active_hour(id, triggers_active_day)

    def active_hour(self, device_id, triggers):
        Domoticz.Debug(f"Nb déclencheurs = {len(triggers)}")
        m = 0
        nw = now.time()
        if len(triggers) > 1:
            while not (strToTime(triggers[m]) <= nw <= strToTime(triggers[m+1])):
                #print(f" i = {m}, a = {triggers[m]}, now time = {nw}, str_time = {strToTime(triggers[m])}")
                if m + 2 < len(triggers):
                    m = m + 1
                else:
                    m = m + 1
                    break

        Domoticz.Debug(f" i = {m}, a = {triggers[m]}, now time = {nw}, str_time = {strToTime(triggers[m])}")
        self.update_device(str(device_id), triggers[m])   
        
    def update_device(self, device_id, trigger):
        Domoticz.Debug("update_device:" + device_id)
        cmd = '/json.htm?type=devices&rid=' + device_id
        result = self.request(cmd)
        if result:
            deviceJson =  result['result'][0]
            Domoticz.Debug(f'status {device_id}: {deviceJson} ')
            
            status = 'On'
            prop = 'Status'
            selectorType = (deviceJson['SwitchType'] == "Selector")
            if selectorType:
                prop = 'Level'
                status = trigger['Level']
            else:
                status = 'On' if trigger['TimerCmd']==0 else 'Off'
                
            if (status != deviceJson[prop]):    
                cmd = '/json.htm?type=command&param=switchlight&idx=' + device_id + '&switchcmd=' + ('Set%20Level&level=' if  selectorType else '') + str(status)
                if self.request(cmd):
                    Domoticz.Log(f'device {device_id} changes to {status} status')
                    # return True
            else:
                Domoticz.Log(f'device {device_id} already on good state')
                        
    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        
        Domoticz.Heartbeat(30)
        DumpConfigToLog()                                

        self.get_timer_list(Parameters["Address"],Parameters["Port"])
            
    def onStop(self):
        Domoticz.Log("Plugin is stopping.")
   
#    def onHeartbeat(self):     
#        Domoticz.Debug("onHeartbeat")

#    def onCommand(self, Unit, Command, Level, Hue):
#        Domoticz.Debug("Data:" + str(Data))
       
    def onDisconnect(self, Connection):
        Domoticz.Log("Device has disconnected")
                            

global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

#def onConnect(Connection, Status, Description):
#    global _plugin
#    _plugin.onConnect(Connection, Status, Description)

#def onMessage(Connection, Data):
#    global _plugin
#    _plugin.onMessage(Connection, Data)

#def onCommand(Unit, Command, Level, Hue):
#    global _plugin
#    _plugin.onCommand(Unit, Command, Level, Hue)

#def onHeartbeat():
#    global _plugin
#    #_plugin.onHeartbeat()

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
            
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
                
    return
    
def byTime(obj):
    return obj['Time']

def strToTime(trigger):
    #return datetime.strptime(trigger['Time'], '%H:%M').time()
    val = trigger['Time']
    return datetime.time(hour=int(val.split(':')[0]),minute=int(val.split(':')[1]),second=0)
