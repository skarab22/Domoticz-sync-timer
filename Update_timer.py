# import json
from datetime import datetime
import requests

host = 'http://192.168.1.20'
port = ':9090'
now = datetime.now()


def url(json_cmd):
    return host + port + json_cmd


def request(json_cmd):
    response = requests.get(url(json_cmd))
    if response.ok:
        return response.json()


def get_timer(device_id):
    str_id = str(device_id)
    cmd = '/json.htm?idx=' + str_id + '&type=timers'
    return request(cmd)


def get_timer_list():
    cmd = '/json.htm?type=schedules&filter=device'
    result = request(cmd)
    timer_list_id = []

    for i in result['result']:
        timer_list_id.append(i['DeviceRowID'])

    timer_list_id = set(timer_list_id)
    print(f" timer_list_id = {timer_list_id}")
    return timer_list_id


def device_level_uptodate(device_id, timer_level):
    cmd = '/json.htm?type=devices&rid=' + device_id
    if request(cmd):
        result = request(cmd)
        print('true request cmd')
        if timer_level != result['result'][0]['Level']:
            return True
        else:
            return False


def update_device(device_id, timer_level):
    if device_level_uptodate(device_id, timer_level):
        cmd = '/json.htm?type=command&param=switchlight&idx=' + device_id + '&switchcmd=Set%20Level&level=' + timer_level
        if request(cmd):
            result = request(cmd)
            print("ok")
            # return True
    else:
        print('device already on good state')


# a implémenter :
# une fonction qui trie par heure croissante
# puis on vérifie les jours
# puis on vérifie les heures
def byTime(obj):
    return obj['Time']


def active_day(list_id):
    for i in list_id:
        print(f"entré dans la fonction active_timer avec l'ID = {i}")
        d_timer = get_timer(i)
        sort_dtimer = sorted(d_timer['result'], key=byTime)
        print(f"Il y a {len(sort_dtimer)} timer pour l'idx {i} ")
        timer_day_active = []
        # for j in range(len(device_timer['result'])):
        for j, k in enumerate(sort_dtimer):
            print(f"Days = {k['Days']}")
            if k['Days'] == 128:
                print('Timer actif tous les jours')
                bin_active_day = '1111111'
            elif k['Days'] == 256:
                print('Timer actif jours de semaine')
                bin_active_day = '0011111'
            elif k['Days'] == 512:
                print('Timer actif le weekend')
                bin_active_day = '1100000'
            else:
                bin_active_day = format(k['Days'], 'b').zfill(7)
            print(f"Nous somme le {now.weekday()}e jour de la semaine. Valeur Days en binaire = {bin_active_day}")
            print(f"on regarde l'indice {now.weekday()} de la valeur précédente = {bin_active_day[6 - now.weekday()]}")
            if bin_active_day[6 - now.weekday()] == '1':
                timer_day_active.append(j)

        if timer_day_active:
            print(f"ID des timer actifs pour ce jours de la semaine : {timer_day_active}")
            active_hour(i, timer_day_active, sort_dtimer)
        print('')
        # ballayer les heure pour trouver l'heure active


def update_str_time_idx(index, timer, id_list):
    a = id_list[index]
    str_time = datetime.strptime(timer[a]['Time'], '%H:%M')
    return str_time


def active_hour(device_id, act_days, timer):
    print(f"longueur de active day = {len(act_days)}")
    m = 0
    if len(act_days) > 1:
        while not (update_str_time_idx(m, timer, act_days).time() <= now.time() <= update_str_time_idx(m + 1, timer,
                                                                                                       act_days).time()):
            print(
                f" i = {m}, a = {act_days[m]}, now time = {now.time()}, str_time = {update_str_time_idx(m, timer, act_days).time()}")
            if m + 2 < len(act_days):
                m = m + 1
            else:
                m = m + 1
                break

    print(
        f" i = {m}, a = {act_days[m]}, now time = {now.time()}, str_time = {update_str_time_idx(m, timer, act_days).time()}")
    # update_device(str(device_id), str(timer[m]['Level']))


idx = get_timer_list()
active_day(idx)
