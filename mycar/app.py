import os
import subprocess
import time
import json
import socket
import struct
import fcntl
from flask import Flask, request, jsonify, views
from flask_cors import *
from threading import Thread

from dellcar.parts.bluetoothctl import Bluetoothctl
from dellcar.parts.drive import Drive
#from drive import Drive

app = Flask(__name__)
CORS(app, supports_credentials=True)

blt = None


@app.route('/bluetooth')
def connect_bluetooth():
    global blt
    try:
        if os.path.exists("/dev/input/js0"):
            return "Joystick has connected, please disconnect first"
        print("Init bluetooth...")
        bl = Bluetoothctl()
        print("Ready!")
        out = bl.start_scan()
        disc = []
        for o in out:
            if "Wireless Controller" in str(o):
                bl.stop_scan()
				
                mac = str(o).split(" ")[2]
                disc.append(mac)
        for m in disc:
            print("disc",disc)
            try:
                process = subprocess.Popen(
                    "echo 'trust {}' | bluetoothctl".format(mac), stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, shell=True
                )
                output, _ = process.communicate()

                if process.returncode > 0:
                    return output
                time.sleep(2)
                print("try1",m)
                try:
                    cnt = bl.connect(m)
                    print("try11",cnt)
                except Exception as e:
                    print(e)
                    print("continue")
                    continue
                if cnt:
                    print("success")
                    return "success"
                else:
                    continue
            except Exception as e:
                print(e)
                return "connect failed, please try again"
    except Exception as e:
        print(e)
    blt = None
    return "connect failed, please try again"


@app.route('/manual')
def manual_drive():
    #if not os.path.exists("/dev/input/js0"):
    #    return "Please connect you joystick first"
    print(Drive.stats)
    if Drive.stats:
        return "Another process is running, please stop it and try again"
    mal_div = Drive()
    t = Thread(target=mal_div.drive)
    t.start()
    for i in range(30):
        if Drive.stats == "green":
            return "success"
        else:
            time.sleep(1)
    return "failed"


@app.route('/auto', methods=['POST'])
def auto_drive():
    if Drive.stats:
        return "Another process is running, please stop it and try again"
    # path = request.form.get("path")
    path = os.path.join("/home/mousika/mycar/models", json.loads(request.get_data(as_text=True))["path"])
    print(path)
    if not path:
        return "path can't be empty"
    if not os.path.exists(path):
        return "Path does not exist, please use true path"
    aut_div = Drive()
    t = Thread(target=aut_div.drive, args=(path,))
    t.start()
    for i in range(30):
        if Drive.stats == "green":
            return "success"
        else:
            time.sleep(1)
    return "failed"


@app.route('/status')
def get_stats():
    stats = Drive.stats
    if stats == "yellow":
        return "yellow"
    elif stats == "green":
        return "green"
    elif not stats:
        return "gray"
    else:
        return "red"


def stop():
    Drive.stop = True
    Drive.stats = None


@app.route('/stop')
def drive_stop():
    if not Drive.stats:
        return "No running process"
    Drive.stop = True
    Drive.stats = None
    time.sleep(1)
    t = Thread(target=stop)
    t.start()
    return "success"


@app.route('/wifi', methods=['POST'])
def wifi_connect():
    data = json.loads(request.get_data(as_text=True))
    ssid = data["SSID"]
    psk = data["password"]
    # ssid = request.form.get("SSID")
    # psk = request.form.get("password")

    if not ssid or not psk:
        return "SSID or password can't be empty"
    process = subprocess.Popen(
        "sudo nmcli dev wifi connect {} password {}".format(ssid, psk), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, shell=True
    )
    output, _ = process.communicate()

    if process.returncode > 0:
        print(output)
        try:
            process = subprocess.Popen(
                "nmcli dev wif | grep -v grep | awk '{print $2}'", stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True
               )
            output_, _ = process.communicate()
            if process.returncode > 0:
                return output_
            current_ssid = str(output_).split('\\n')[1]
            print(current_ssid)
            process = subprocess.Popen(
                "sudo nmcli dev dis wlan0", stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True
               )
            output_, _ = process.communicate()
            if process.returncode > 0:
                print(output_)
                return output_
            time.sleep(3)
            process = subprocess.Popen(
                "sudo nmcli dev wifi connect {} password {}".format(ssid, psk), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True
                )
            output_, _ = process.communicate()
            if process.returncode > 0:
                return output_
        except Exception as e:
            print(e)
            return output

    process = subprocess.Popen(
        "sudo nmcli con modify {} connection.permissions ''".format(ssid).format(ssid, psk), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, shell=True
    )
    output, _ = process.communicate()

    if process.returncode > 0:
        return output

    ip = get_host_ip('wlan0')
    return "connect wifi {} success, your wifi ipaddress is {}".format(ssid, ip)


def get_host_ip(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes(ifname[:15].encode('utf-8')))
        )[20:24])

    except Exception as e:
        print(e)


@app.route('/list_models', methods=["GET"])
def list_models():
    try:
        model_list = []
        for model in os.listdir("models"):
            if not model.endswith(".pb") or not model.endswith(".metadata"):
                model_list.append(model)
        data = {"models": model_list}
        return jsonify(data)
    except Exception as e:
        print(e)


class StaticIp(views.MethodView):
    def __init__(self):
        self.ssid = ""

    def get(self):
        process = subprocess.Popen(
            "sudo nmcli con up '{}'".format(self.ssid), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True
        )
        output, _ = process.communicate()

        if process.returncode > 0:
            return output
        self.ssid = ""
        return "success"

    def post(self):
        data = json.loads(request.get_data(as_text=True))
        ssid = data["SSID"]
        self.ssid = ssid
        ip = data["ip"]
        gateway = data["gateway"]
        dns = data["dns"]
        if not ssid or not ip:
            return "ssid or ip can't be empty"
        process = subprocess.Popen(
            "sudo nmcli con mod '{}' ipv4.addresses {}/24".format(ssid, ip), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True
        )
        output, _ = process.communicate()

        if process.returncode > 0:
            return output
        process = subprocess.Popen(
            "sudo nmcli con mod '{}' ipv4.gateway {}".format(ssid, gateway), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True
        )
        output, _ = process.communicate()

        if process.returncode > 0:
            return output

        process = subprocess.Popen(
            "sudo nmcli con mod '{}' ipv4.dns {}".format(ssid, dns), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True
        )
        output, _ = process.communicate()

        if process.returncode > 0:
            return output

        process = subprocess.Popen(
            "sudo nmcli con mod '{}' ipv4.method manual".format(ssid), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True
        )
        output, _ = process.communicate()

        if process.returncode > 0:
            return output
        return "success"


app.add_url_rule('/static', view_func=StaticIp.as_view('staticip'))

# @app.route('/static_ip', methods=['GET', 'POST'])
# def change_ip():
#     if request.method == 'GET':
#         process = subprocess.Popen(
#             "sudo nmcli con up '{}'".format(SSID), stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT, shell=True
#         )
#         output, _ = process.communicate()
#
#         if process.returncode > 0:
#             return output
#         return "success"
#     else:
#         data = json.loads(request.get_data(as_text=True))
#         ssid = data["SSID"]
#         ip = data["ip"]
#         gateway = data["gateway"]
#         dns = data["dns"]
#         if not ssid or not ip:
#             return "ssid or ip can't be empty"
#         process = subprocess.Popen(
#             "sudo nmcli con mod '{}' ipv4.addresses {}/24".format(ssid, ip), stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT, shell=True
#         )
#         output, _ = process.communicate()
#
#         if process.returncode > 0:
#             return output
#         process = subprocess.Popen(
#             "sudo nmcli con mod '{}' ipv4.gateway {}".format(ssid, gateway), stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT, shell=True
#         )
#         output, _ = process.communicate()
#
#         if process.returncode > 0:
#             return output
#
#         process = subprocess.Popen(
#             "sudo nmcli con mod '{}' ipv4.dns {}".format(ssid, dns), stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT, shell=True
#         )
#         output, _ = process.communicate()
#
#         if process.returncode > 0:
#             return output
#
#         process = subprocess.Popen(
#             "sudo nmcli con mod '{}' ipv4.method manual".format(ssid), stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT, shell=True
#         )
#         output, _ = process.communicate()
#
#         if process.returncode > 0:
#             return output
#         return "success"


if __name__ == '__main__':
    app.run(host="127.0.0.1")
