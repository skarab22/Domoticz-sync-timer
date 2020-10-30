# import json
from datetime import datetime
import requests

host = 'http://192.168.1.20'
port = ':9090'
now = datetime.now()

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

def url(json_cmd):
    return host + port + json_cmd


def request(json_cmd):
    response = requests.get(url(json_cmd))
    if response.ok:
        return response.json()

def get_timer_list():
    cmd = '/json.htm?type=schedules&filter=device'
    timers = request(cmd)['result']
    print(f"timers:{timers}")
   
    #on filtre les timers actifs
    activeTimers = [timer for timer in timers if timer['Active'] == "true"]
    
    print(f"activeTimers:{activeTimers}")
    
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
        
    print(f"timer_kvp:{timer_kvp}")

    return timer_kvp


def update_device(device_id, trigger):
    cmd = '/json.htm?type=devices&rid=' + device_id
    if request(cmd):
        result = request(cmd)
        deviceJson =  result['result'][0]
        #print(f'status {device_id}: {deviceJson} ')
        
        status = 'On'
        prop = 'Status'
        selectorType = (deviceJson['SwitchType'] == "Selector")
        if selectorType:
            prop = 'Level'
            status = trigger['Level']
        else:
            status = 'On' if trigger['Level']==100 else 'Off'
            
        if (status != deviceJson[prop]):    
            cmd = '/json.htm?type=command&param=switchlight&idx=' + device_id + '&switchcmd=' + ('Set%20Level&level=' if  selectorType else '') + str(status)
            if request(cmd):
                #result = request(cmd)
                print(f'device {device_id} changes to {status} status')
                # return True
        else:
            print(f'device {device_id} already on good state')


def byTime(obj):
    return obj['Time']


def active_day(list_id):
    day = now.weekday()
    for id,timers in list_id.items():
        print(f"entre dans la fonction active_timer avec l'ID = {id}")
        triggers = sorted(timers, key=byTime)
        print(f"Il y a {len(triggers)} timer pour l'idx {id} ")
        triggers_active_day = []
        
        for j, k in enumerate(triggers):
            print(f"Days = {k['Days']}")
            if k['Days'] == EVERYDAYS:
                print('Timer actif tous les jours')
                bin_active_day = SUM_EVERYDAYS
            elif k['Days'] == WEEKDAYS:
                print('Timer actif jours de semaine')
                bin_active_day = SUM_WEEKDAYS
            elif k['Days'] == WEEKENDS:
                print('Timer actif le weekend')
                bin_active_day = SUM_WEEKENDS
            else:
                bin_active_day = int(k['Days'])
            print(f"Nous somme le {day}e jour de la semaine. Valeur Days en binaire = {2**day}")
            if bin_active_day & (2**day) :
                triggers_active_day.append(k)

        if triggers:
            print(f"ID des timer actifs pour ce jours de la semaine : {triggers_active_day}")
            active_hour(id, triggers_active_day)
        print('')
        # ballayer les heure pour trouver l'heure active


def strToTime(trigger):
    return datetime.strptime(trigger['Time'], '%H:%M').time()


def active_hour(device_id, triggers):
    print(f"Nb déclencheurs = {len(triggers)}")
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

    print(f" i = {m}, a = {triggers[m]}, now time = {nw}, str_time = {strToTime(triggers[m])}")
    update_device(str(device_id), triggers[m])


idx = get_timer_list()
active_day(idx)
