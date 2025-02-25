#!/usr/bin/env python

import argparse
from re import X
from gi.repository import GLib as gobject
import platform
import argparse
import logging
import sys
import os
import time
import datetime
import serial
import struct
import binascii
import json

# setup timezone
os.environ["TZ"] = "Europe/Berlin"

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
# filename='log.txt')

# connect and register to dbus
driver = {
    "name": "LIONTRON BMS",
    "servicename": "liontron",
    "instance": 1,
    "id": 0x01,
    "version": 1.1,
    "serial": "LIONBMS",
    "connection": "com.victronenergy.battery.ttyLIONBMS01",
}


parser = argparse.ArgumentParser(description="LIONTRON BMS driver")
parser.add_argument(
    "--version",
    action="version",
    version="%(prog)s v" + str(driver["version"]
                               ) + " (" + driver["serial"] + ")",
)
parser.add_argument("--debug", action="store_true",
                    help="enable debug logging")
parser.add_argument(
    "--test", action="store_true", help="test some stored examples network packets"
)
parser.add_argument(
    "--victron", action="store_true", help="enable Victron DBUS support for VenusOS"
)
parser.add_argument(
    "--json", action="store_true", help="print NDJSON reports to stdout"
)
parser.add_argument(
    "--interval", default=1.0,type=float, help="reporting interval in seconds. "
    "negative value: report once only"
)
requiredArguments = parser.add_argument_group("required arguments")
requiredArguments.add_argument(
    "-d", "--device", help="serial device for data (eg /dev/ttyUSB0)", required=True
)
args = parser.parse_args()

serial_port = serial.Serial(args.device, 9600, timeout=1)
serial_port.flushInput()
logging.info(serial_port.name)


# victron stuff should be used
if args.victron:

    # Victron packages
    sys.path.insert(1, os.path.join(
        os.path.dirname(__file__), "./ext/velib_python"))
    from vedbus import VeDbusService

    from dbus.mainloop.glib import DBusGMainLoop

    DBusGMainLoop(set_as_default=True)

    dbusservice = VeDbusService(driver["connection"])

    # Create the management objects, as specified in the ccgx dbus-api document
    dbusservice.add_path("/Mgmt/ProcessName", __file__)
    dbusservice.add_path(
        "/Mgmt/ProcessVersion", "Unknown and Python " + platform.python_version()
    )
    dbusservice.add_path("/Mgmt/Connection", driver["connection"])

    # Create the mandatory objects
    dbusservice.add_path("/DeviceInstance", driver["instance"])
    dbusservice.add_path("/ProductId", driver["id"])
    dbusservice.add_path("/ProductName", driver["name"])
    dbusservice.add_path("/FirmwareVersion", driver["version"])
    dbusservice.add_path("/HardwareVersion", driver["version"])
    dbusservice.add_path("/Serial", driver["serial"])
    dbusservice.add_path("/Connected", 1)

    # Create device list
    dbusservice.add_path("/Devices/0/DeviceInstance", driver["instance"])
    dbusservice.add_path("/Devices/0/FirmwareVersion", driver["version"])
    dbusservice.add_path("/Devices/0/ProductId", driver["id"])
    dbusservice.add_path("/Devices/0/ProductName", driver["name"])
    dbusservice.add_path("/Devices/0/ServiceName", driver["servicename"])
    dbusservice.add_path("/Devices/0/VregLink", "(API)")

    dbusservice.add_path("/Alarms/LowVoltage", 0)
    dbusservice.add_path("/Alarms/HighVoltage", 0)
    dbusservice.add_path("/Alarms/LowSoc", 0)
    dbusservice.add_path("/Alarms/HighChargeCurrent", 0)
    dbusservice.add_path("/Alarms/HighDischargeCurrent", 0)
    dbusservice.add_path("/Alarms/HighChargeTemperature", 0)
    dbusservice.add_path("/Alarms/LowChargeTemperature", 0)

    # Create the chargery bms paths
    dbusservice.add_path("/Info/Soc", -1)
    dbusservice.add_path("/Info/CurrentMode", -1)
    dbusservice.add_path("/Info/Current", -1)
    dbusservice.add_path("/Info/Temp/Sensor1", -1)
    dbusservice.add_path("/Info/Temp/Sensor2", -1)
    dbusservice.add_path("/Info/ChargeEndVoltage", -1)
    dbusservice.add_path("/Info/UpdateTimestamp", -1)
    dbusservice.add_path("/Info/Balance1", -1)
    dbusservice.add_path("/Info/Balance2", -1)
    dbusservice.add_path("/Info/Balance3", -1)
    dbusservice.add_path("/Info/Balance4", -1)
    dbusservice.add_path("/Info/Mosfet", -1)
    dbusservice.add_path("/Info/NumberOfCells", -1)
    dbusservice.add_path("/Info/Cycles", -1)
    dbusservice.add_path("/Info/ProtectionState", -1)
    dbusservice.add_path("/Info/Eta", -1)
    dbusservice.add_path("/Dc/0/Voltage", -1)
    dbusservice.add_path("/Dc/0/Current", -1)
    dbusservice.add_path("/Dc/0/Power", -1)
    dbusservice.add_path("/Dc/0/Temperature", -1)
    dbusservice.add_path("/AirTemperature", -1)
    dbusservice.add_path("/Soc", -1)
    dbusservice.add_path("/Voltages/Cell1", -1)
    dbusservice.add_path("/Voltages/Cell2", -1)
    dbusservice.add_path("/Voltages/Cell3", -1)
    dbusservice.add_path("/Voltages/Cell4", -1)
    dbusservice.add_path("/Voltages/Sum", -1)
    dbusservice.add_path("/Voltages/Diff", -1)
    dbusservice.add_path("/Voltages/Max", -1)
    dbusservice.add_path("/Voltages/Min", -1)
    dbusservice.add_path("/Voltages/BatteryCapacityWH", -1)
    dbusservice.add_path("/Voltages/BatteryCapacityAH", -1)
    dbusservice.add_path("/Voltages/BatteryNominalAH", -1)
    dbusservice.add_path("/Voltages/UpdateTimestamp", -1)

    # Create the real values paths
    dbusservice.add_path("/Raw/Info/Soc", -1)
    dbusservice.add_path("/Raw/Info/CurrentMode", -1)
    dbusservice.add_path("/Raw/Info/Current", -1)
    dbusservice.add_path("/Raw/Info/Temp/Sensor1", -1)
    dbusservice.add_path("/Raw/Info/Temp/Sensor2", -1)
    dbusservice.add_path("/Raw/Info/ChargeEndVoltage", -1)
    dbusservice.add_path("/Raw/Info/UpdateTimestamp", -1)
    dbusservice.add_path("/Raw/Info/Eta", -1)
    dbusservice.add_path("/Raw/Voltages/Cell1", -1)
    dbusservice.add_path("/Raw/Voltages/Cell2", -1)
    dbusservice.add_path("/Raw/Voltages/Cell3", -1)
    dbusservice.add_path("/Raw/Voltages/Cell4", -1)
    dbusservice.add_path("/Raw/Voltages/Sum", -1)
    dbusservice.add_path("/Raw/Voltages/Diff", -1)
    dbusservice.add_path("/Raw/Voltages/Max", -1)
    dbusservice.add_path("/Raw/Voltages/Min", -1)
    dbusservice.add_path("/Raw/Voltages/BatteryCapacityWH", -1)
    dbusservice.add_path("/Raw/Voltages/BatteryCapacityAH", -1)
    dbusservice.add_path("/Raw/Voltages/BatteryNominalAH", -1)
    dbusservice.add_path("/Raw/Voltages/UpdateTimestamp", -1)


PACKET_LENGTH_MINIMUM = 7

BMS_STATUS = {
    "bms": {
        "charged_end_voltage": {"value": -1.000, "text": ""},
        "current_mode": {"value": -1, "text": ""},
        "current": {"value": -1, "text": ""},
        "temperature": {
            "sensor_t1": {"value": -1.00, "text": ""},
            "sensor_t2": {"value": -1.00, "text": ""},
        },
        "soc": {"value": -1, "text": ""},
        "eta": {"value": -1, "text": ""},
        "timestamp": {"value": -1, "text": ""},
        "balance_1": {"value": -1, "text": ""},
        "balance_2": {"value": -1, "text": ""},
        "balance_3": {"value": -1, "text": ""},
        "balance_4": {"value": -1, "text": ""},
        "mosfet": {"value": -1, "text": ""},
        "number_of_cells": {"value": -1, "text": ""},
        "cycles": {"value": -1, "text": ""},
        "protection_state": {"value": -1, "text": ""},
    },
    "voltages": {
        "cell1_voltage": {"value": -1, "text": ""},
        "cell2_voltage": {"value": -1, "text": ""},
        "cell3_voltage": {"value": -1, "text": ""},
        "cell4_voltage": {"value": -1, "text": ""},
        "agg_voltages": {
            "sum": {"value": -1, "text": ""},
            "max": {"value": -1, "text": ""},
            "min": {"value": -1, "text": ""},
            "diff": {"value": -1, "text": ""},
        },
        "battery_capacity_wh": {"value": -1, "text": ""},
        "battery_capacity_ah": {"value": -1, "text": ""},
        "battery_nominal_ah": {"value": -1, "text": ""},
        "timestamp": {"value": -1, "text": ""},
    },
}

SPECIAL_DISPLAY_SYMBOLS = {"degree": u"\u00b0", "ohm": u"\u03A9"}


def reset_status_values():

    BMS_STATUS["bms"]["charged_end_voltage"]["value"] = -1
    BMS_STATUS["bms"]["charged_end_voltage"]["text"] = ""
    BMS_STATUS["bms"]["current_mode"]["value"] = -1
    BMS_STATUS["bms"]["current_mode"]["text"] = ""
    BMS_STATUS["bms"]["current"]["value"] = -1
    BMS_STATUS["bms"]["current"]["text"] = ""
    BMS_STATUS["bms"]["temperature"]["sensor_t1"]["value"] = -1
    BMS_STATUS["bms"]["temperature"]["sensor_t1"]["text"] = ""
    BMS_STATUS["bms"]["temperature"]["sensor_t2"]["value"] = -1
    BMS_STATUS["bms"]["temperature"]["sensor_t2"]["text"] = ""
    BMS_STATUS["bms"]["soc"]["value"] = -1
    BMS_STATUS["bms"]["soc"]["text"] = ""
    BMS_STATUS["bms"]["eta"]["value"] = -1
    BMS_STATUS["bms"]["eta"]["text"] = ""
    BMS_STATUS["bms"]["timestamp"]["value"] = -1
    BMS_STATUS["bms"]["timestamp"]["text"] = ""
    BMS_STATUS["bms"]["balance_1"]["value"] = -1
    BMS_STATUS["bms"]["balance_1"]["text"] = ""
    BMS_STATUS["bms"]["balance_2"]["value"] = -1
    BMS_STATUS["bms"]["balance_2"]["text"] = ""
    BMS_STATUS["bms"]["balance_3"]["value"] = -1
    BMS_STATUS["bms"]["balance_3"]["text"] = ""
    BMS_STATUS["bms"]["balance_4"]["value"] = -1
    BMS_STATUS["bms"]["balance_4"]["text"] = ""
    BMS_STATUS["bms"]["mosfet"]["value"] = -1
    BMS_STATUS["bms"]["mosfet"]["text"] = ""
    BMS_STATUS["bms"]["number_of_cells"]["value"] = -1
    BMS_STATUS["bms"]["number_of_cells"]["text"] = ""


def reset_voltages_values():
    BMS_STATUS["voltages"]["cell1_voltage"]["value"] = -1
    BMS_STATUS["voltages"]["cell1_voltage"]["text"] = ""
    BMS_STATUS["voltages"]["cell2_voltage"]["value"] = -1
    BMS_STATUS["voltages"]["cell2_voltage"]["text"] = ""
    BMS_STATUS["voltages"]["cell3_voltage"]["value"] = -1
    BMS_STATUS["voltages"]["cell3_voltage"]["text"] = ""
    BMS_STATUS["voltages"]["cell4_voltage"]["value"] = -1
    BMS_STATUS["voltages"]["cell4_voltage"]["text"] = ""
    BMS_STATUS["voltages"]["agg_voltages"]["sum"]["value"] = -1
    BMS_STATUS["voltages"]["agg_voltages"]["sum"]["text"] = ""
    BMS_STATUS["voltages"]["agg_voltages"]["max"]["value"] = -1
    BMS_STATUS["voltages"]["agg_voltages"]["max"]["text"] = ""
    BMS_STATUS["voltages"]["agg_voltages"]["min"]["value"] = -1
    BMS_STATUS["voltages"]["agg_voltages"]["min"]["text"] = ""
    BMS_STATUS["voltages"]["agg_voltages"]["diff"]["value"] = -1
    BMS_STATUS["voltages"]["agg_voltages"]["diff"]["text"] = ""
    BMS_STATUS["voltages"]["battery_capacity_wh"]["value"] = -1
    BMS_STATUS["voltages"]["battery_capacity_wh"]["text"] = ""
    BMS_STATUS["voltages"]["battery_capacity_ah"]["value"] = -1
    BMS_STATUS["voltages"]["battery_capacity_ah"]["text"] = ""
    BMS_STATUS["voltages"]["timestamp"]["value"] = -1
    BMS_STATUS["voltages"]["timestamp"]["text"] = ""


def get_voltage_value(val1):
    return float(val1.strip())


def get_remainWh(v, ah):
    return int(v * ah)


def get_remainTime(ah, a):
    if a == 0:
        return -1
    return float(ah/a)


def parse_cellinfo(packet):
    if packet[1] != 4:
        return

    cell1 = float(packet[4] << 8 | packet[5]) / 1000.0
    logging.info("parse packet 4")
    logging.info(cell1)
    BMS_STATUS["voltages"]["cell1_voltage"]["value"] = cell1
    BMS_STATUS["voltages"]["cell1_voltage"]["text"] = (
        "{:.3f}".format(cell1) + "V"
    )
    if args.victron:
        dbusservice["/Voltages/Cell1"] = BMS_STATUS["voltages"][
            "cell1_voltage"
        ]["text"]
        dbusservice["/Raw/Voltages/Cell1"] = BMS_STATUS["voltages"][
            "cell1_voltage"
        ]["value"]
    current_date = datetime.datetime.now()
    BMS_STATUS["voltages"]["timestamp"]["value"] = time.time()
    BMS_STATUS["voltages"]["timestamp"]["text"] = current_date.strftime(
        "%a %d.%m.%Y %H:%M:%S"
    )
    if args.victron:
        dbusservice["/Voltages/UpdateTimestamp"] = BMS_STATUS["voltages"][
            "timestamp"
        ]["text"]
        dbusservice["/Raw/Voltages/UpdateTimestamp"] = BMS_STATUS["voltages"][
            "timestamp"
        ]["value"]
    cell2 = float(packet[6] << 8 | packet[7]) / 1000.0
    BMS_STATUS["voltages"]["cell2_voltage"]["value"] = cell2
    BMS_STATUS["voltages"]["cell2_voltage"]["text"] = (
        "{:.3f}".format(cell2) + "V"
    )
    if args.victron:
        dbusservice["/Voltages/Cell2"] = BMS_STATUS["voltages"][
            "cell2_voltage"
        ]["text"]
        dbusservice["/Raw/Voltages/Cell2"] = BMS_STATUS["voltages"][
            "cell2_voltage"
        ]["value"]
    cell3 = float(packet[8] << 8 | packet[9]) / 1000.0
    BMS_STATUS["voltages"]["cell3_voltage"]["value"] = cell3
    BMS_STATUS["voltages"]["cell3_voltage"]["text"] = (
        "{:.3f}".format(cell3) + "V"
    )
    if args.victron:
        dbusservice["/Voltages/Cell3"] = BMS_STATUS["voltages"][
            "cell3_voltage"
        ]["text"]
        dbusservice["/Raw/Voltages/Cell3"] = BMS_STATUS["voltages"][
            "cell3_voltage"
        ]["value"]
    cell4 = float(packet[10] << 8 | packet[11]) / 1000.0
    BMS_STATUS["voltages"]["cell4_voltage"]["value"] = cell4
    BMS_STATUS["voltages"]["cell4_voltage"]["text"] = (
        "{:.3f}".format(cell4) + "V"
    )
    if args.victron:
        dbusservice["/Voltages/Cell4"] = BMS_STATUS["voltages"][
            "cell4_voltage"
        ]["text"]
        dbusservice["/Raw/Voltages/Cell4"] = BMS_STATUS["voltages"][
            "cell4_voltage"
        ]["value"]


def parse_basicdata(packet):
    if packet[1] != 3:
        return

    logging.info("parse packet 3")
    volt = float(packet[4] << 8 | packet[5]) / 100
    BMS_STATUS["voltages"]["agg_voltages"]["sum"]["value"] = volt
    BMS_STATUS["voltages"]["agg_voltages"]["sum"]["text"] = (
        "{:.2f}".format(BMS_STATUS["voltages"]["agg_voltages"]["sum"]["value"])
        + "V"
    )
    if args.victron:
        dbusservice["/Voltages/Sum"] = BMS_STATUS["voltages"]["agg_voltages"][
            "sum"
        ]["text"]
        dbusservice["/Raw/Voltages/Sum"] = BMS_STATUS["voltages"][
            "agg_voltages"
        ]["sum"]["value"]
        dbusservice["/Dc/0/Voltage"] = BMS_STATUS["voltages"]["agg_voltages"][
            "sum"
        ]["value"]
    reset_status_values()
    soc = float(packet[23])
    BMS_STATUS["bms"]["soc"]["value"] = soc
    BMS_STATUS["bms"]["soc"]["text"] = "{:.0f}".format(soc) + "%"
    if args.victron:
        dbusservice["/Info/Soc"] = BMS_STATUS["bms"]["soc"]["text"]
        dbusservice["/Raw/Info/Soc"] = BMS_STATUS["bms"]["soc"]["value"]
        dbusservice["/Soc"] = BMS_STATUS["bms"]["soc"]["value"]
        # update timestamp
    current_date = datetime.datetime.now()
    BMS_STATUS["bms"]["timestamp"]["value"] = time.time()
    BMS_STATUS["bms"]["timestamp"]["text"] = current_date.strftime(
        "%a %d.%m.%Y %H:%M:%S"
    )
    if args.victron:
        dbusservice["/Info/UpdateTimestamp"] = BMS_STATUS["bms"]["timestamp"][
            "text"
        ]
        dbusservice["/Raw/Info/UpdateTimestamp"] = BMS_STATUS["bms"][
            "timestamp"
        ]["value"]
    temp1 = (
        float((struct.unpack(">h", bytearray(packet[27:29]))[0]) - 2731) / 10.0
    )
    BMS_STATUS["bms"]["temperature"]["sensor_t1"]["value"] = temp1
    BMS_STATUS["bms"]["temperature"]["sensor_t1"]["text"] = (
        "{:.2f}".format(temp1) + SPECIAL_DISPLAY_SYMBOLS["degree"] + "C"
    )
    if args.victron:
        dbusservice["/Info/Temp/Sensor1"] = BMS_STATUS["bms"]["temperature"][
            "sensor_t1"
        ]["text"]
        dbusservice["/Raw/Info/Temp/Sensor1"] = BMS_STATUS["bms"][
            "temperature"
        ]["sensor_t1"]["value"]
        dbusservice["/Dc/0/Temperature"] = BMS_STATUS["bms"]["temperature"][
            "sensor_t1"
        ]["value"]
    temp2 = (
        float((struct.unpack(">h", bytearray(packet[29:31]))[0]) - 2731) / 10.0
    )
    BMS_STATUS["bms"]["temperature"]["sensor_t2"]["value"] = temp2
    BMS_STATUS["bms"]["temperature"]["sensor_t2"]["text"] = (
        "{:.2f}".format(temp2) + SPECIAL_DISPLAY_SYMBOLS["degree"] + "C"
    )
    if args.victron:
        dbusservice["/Info/Temp/Sensor2"] = BMS_STATUS["bms"]["temperature"][
            "sensor_t2"
        ]["text"]
        dbusservice["/Raw/Info/Temp/Sensor2"] = BMS_STATUS["bms"][
            "temperature"
        ]["sensor_t2"]["value"]
        dbusservice["/AirTemperature"] = BMS_STATUS["bms"]["temperature"][
            "sensor_t2"
        ]["value"]
    remainAmp = float(packet[8] << 8 | packet[9]) / 100
    BMS_STATUS["voltages"]["battery_capacity_ah"]["value"] = remainAmp
    BMS_STATUS["voltages"]["battery_capacity_ah"]["text"] = (
        "{:.0f}".format(remainAmp) + "Ah"
    )
    if args.victron:
        dbusservice["/Voltages/BatteryCapacityAH"] = BMS_STATUS["voltages"][
            "battery_capacity_ah"
        ]["text"]
        dbusservice["/Raw/Voltages/BatteryCapacityAH"] = BMS_STATUS["voltages"][
            "battery_capacity_ah"
        ]["value"]
    normalAmp = float(struct.unpack(">h", bytearray(packet[10:12]))[0]) / 100.0
    BMS_STATUS["voltages"]["battery_nominal_ah"]["value"] = normalAmp
    BMS_STATUS["voltages"]["battery_nominal_ah"]["text"] = (
        "{:.0f}".format(normalAmp) + "Ah"
    )
    if args.victron:
        dbusservice["/Voltages/BatteryNominalAH"] = BMS_STATUS["voltages"][
            "battery_nominal_ah"
        ]["text"]
        dbusservice["/Raw/Voltages/BatteryNominalAH"] = BMS_STATUS["voltages"][
            "battery_nominal_ah"
        ]["value"]
    remainWh = remainAmp * volt
    BMS_STATUS["voltages"]["battery_capacity_wh"]["value"] = remainWh
    BMS_STATUS["voltages"]["battery_capacity_wh"]["text"] = (
        "{:.0f}".format(BMS_STATUS["voltages"]["battery_capacity_wh"]["value"])
        + "Wh"
    )
    if args.victron:
        dbusservice["/Voltages/BatteryCapacityWH"] = BMS_STATUS["voltages"][
            "battery_capacity_wh"
        ]["text"]
        dbusservice["/Raw/Voltages/BatteryCapacityWH"] = BMS_STATUS["voltages"][
            "battery_capacity_wh"
        ]["value"]
    amp = float(struct.unpack(">h", bytearray(packet[6:8]))[0]) / 100.0
    BMS_STATUS["bms"]["current"]["value"] = amp
    BMS_STATUS["bms"]["current"]["text"] = (
        str(BMS_STATUS["bms"]["current"]["value"]) + "A")
    if args.victron:
        dbusservice["/Info/Current"] = BMS_STATUS["bms"]["current"]["text"]
        dbusservice["/Raw/Info/Current"] = BMS_STATUS["bms"]["current"]["value"]
        dbusservice["/Dc/0/Current"] = BMS_STATUS["bms"]["current"]["value"]

    if abs(amp) == amp:
        remainTime = get_remainTime(normalAmp-remainAmp, amp)
        prefix = " voll um "
    else:
        remainTime = get_remainTime(remainAmp, abs(amp))
        prefix = " leer um "
    logging.info(prefix + str(remainTime))
    BMS_STATUS["bms"]["eta"]["value"] = remainTime
    if remainTime == -1:
        BMS_STATUS["bms"]["eta"]["text"] = "--"
    else:
        remainT = current_date + datetime.timedelta(seconds=remainTime*3600)
        BMS_STATUS["bms"]["eta"]["text"] = prefix + remainT.strftime(
        "%a %d.%m.%Y %H:%M:%S")

    if args.victron:
        dbusservice["/Info/Eta"] = BMS_STATUS["bms"]["eta"]["text"]
        dbusservice["/Raw/Info/Eta"] = BMS_STATUS["bms"]["eta"]["text"]

    watt = (
        BMS_STATUS["bms"]["current"]["value"]
        * BMS_STATUS["voltages"]["agg_voltages"]["sum"]["value"]
    )
    if args.victron:
        dbusservice["/Dc/0/Power"] = watt

    cell_count = packet[25]
    BMS_STATUS["bms"]["number_of_cells"]["value"] = cell_count
    BMS_STATUS["bms"]["number_of_cells"]["text"] = str(cell_count)
    if args.victron:
        dbusservice["/Info/NumberOfCells"] = BMS_STATUS["bms"][
            "number_of_cells"
        ]["text"]
    cycles = struct.unpack(">h", bytearray(packet[12:14]))[0]
    BMS_STATUS["bms"]["cycles"]["text"] = cycles
    if args.victron:
        dbusservice["/Info/Cycles"] = BMS_STATUS["bms"]["cycles"]["text"]
    protectionByte1 = packet[20]
    protectionBits1 = bin(protectionByte1)[2:].rjust(8, "0")
    protectionText = "Kein Fehler"
    if protectionBits1[0] == 1:
        protectionText = "Zellen-Spg zu hoch"
    if protectionBits1[1] == 1:
        protectionText = "Unterspannung"
    if protectionBits1[2] == 1:
        protectionText = "Gruppen-Spg. zu hoch"
    if protectionBits1[3] == 1:
        protectionText = "Gruppen-Spg. zu niedrig"
    if protectionBits1[4] == 1:
        protectionText = "Lade-Temp zu hoch"
    if protectionBits1[5] == 1:
        protectionText = "Lade-Temp zu niedrig"
    if protectionBits1[6] == 1:
        protectionText = "Entlade-Temp zu hoch"
    if protectionBits1[7] == 1:
        protectionText = "Entlade-Temp zu niedrig"
    protectionByte2 = packet[21]
    protectionBits2 = bin(protectionByte2)[2:].rjust(8, "0")
    protectionText = "Kein Fehler"
    if protectionBits2[0] == 1:
        protectionText = "Lade-Strom zu hoch"
    if protectionBits2[1] == 1:
        protectionText = "Entlade-Strom zu hoch"
    if protectionBits2[2] == 1:
        protectionText = "Kurzschluss"
    if protectionBits2[3] == 1:
        protectionText = "IC Error"
    if protectionBits2[4] == 1:
        protectionText = "Software Lock"
    BMS_STATUS["bms"]["protection_state"]["text"] = protectionText
    if args.victron:
        dbusservice["/Info/ProtectionState"] = BMS_STATUS["bms"][
            "protection_state"
        ]["text"]

    if args.victron:
        dbusservice["/Alarms/HighChargeTemperature"] = protectionBits1[4]
        dbusservice["/Alarms/LowChargeTemperature"] = protectionBits1[5]
        dbusservice["/Alarms/HighDischargeCurrent"] = protectionBits2[1]
        dbusservice["/Alarms/HighChargeCurrent"] = protectionBits2[0]
        dbusservice["/Alarms/HighVoltage"] = protectionBits1[2]
        dbusservice["/Alarms/LowVoltage"] = protectionBits1[3]
        if soc <= 16:
            dbusservice["/Alarms/LowSoc"] = 1
        else:
            dbusservice["/Alarms/LowSoc"] = 0
    balanceByte = packet[16]
    balanceBits = bin(balanceByte)[2:].rjust(8, "0")
    BMS_STATUS["bms"]["balance_1"]["text"] = balanceBits[0]
    if args.victron:
        dbusservice["/Info/Balance1"] = BMS_STATUS["bms"]["balance_1"]["text"]
    BMS_STATUS["bms"]["balance_2"]["text"] = balanceBits[1]
    if args.victron:
        dbusservice["/Info/Balance2"] = BMS_STATUS["bms"]["balance_2"]["text"]
    BMS_STATUS["bms"]["balance_3"]["text"] = balanceBits[2]
    if args.victron:
        dbusservice["/Info/Balance3"] = BMS_STATUS["bms"]["balance_3"]["text"]
    BMS_STATUS["bms"]["balance_4"]["text"] = balanceBits[3]
    if args.victron:
        dbusservice["/Info/Balance4"] = BMS_STATUS["bms"]["balance_4"]["text"]



def parse_bmsinfo(packet):
    if packet[1] != 5:
        return

    logging.info("parse packet 5")

    len = int(packet[2] << 8 | packet[3])
    logging.debug("content length " + str(len))
    serial = (packet[4:len+4]).decode("utf-8")
    logging.info("serial number " + serial)

    if args.victron:
        dbusservice["/Serial"] = serial


def validate_data(buffer: bytes):
    logging.debug(binascii.hexlify(buffer))
    if (len(buffer)==0):
        return False

    if (buffer[0] != 0xdd):
        logging.error("no SOR found")
        return False

    if (buffer[len(buffer)-1] != 0x77):
        logging.error("no EOR found")
        return False

    logging.debug("command data received: " + str(buffer[1]))

    content_len = int(buffer[2] << 8 | buffer[3])
    logging.debug("data length received: " + str(content_len))

    if (content_len > len(buffer)-7):
        logging.error("content length larger than buffer size")
        logging.info(binascii.hexlify(buffer))
        return False

    data = buffer[2:-3]
    checksum_received = buffer[-3:-1]

    logging.debug("received checksum: " + str(checksum_received))

    checksum_calc = 0x10000

    for b in data:
        checksum_calc = checksum_calc - int(b)

    crc_b = checksum_calc.to_bytes(2, byteorder='big')
    logging.debug("calculated checksum: " + str(crc_b))

    if checksum_received != crc_b:
        logging.error("Checksum missmatch")
        logging.info(binascii.hexlify(buffer))
        if args.victron:
            dbusservice["/Info/ProtectionState"] = "BMS Kommunikationsfehler. Fehlerhafte Daten empfangen."

    return checksum_received == crc_b


def receive_data(cmd: bytearray):
    try:
        serial_port.flushOutput()
        serial_port.flushInput()
        serial_port.write(serial.to_bytes(cmd))
        serial_packet = bytearray()
        time.sleep(.5)
        if serial_port.in_waiting > 0:
            logging.debug(
                "Data Waiting [" + str(serial_port.in_waiting) + " bytes]")
            if serial_port.in_waiting >= (PACKET_LENGTH_MINIMUM * 2):
                data_buffer_array = serial_port.read(serial_port.in_waiting)
                logging.debug(
                    "Data Received [" + str(len(data_buffer_array)) + " bytes]"
                )
            
                serial_packet.extend(data_buffer_array)

            if validate_data(serial_packet):
                logging.debug("receive DATA")

                return serial_packet
            else:
                return bytearray()
        
        return bytearray()
    except:
        raise


def handle_serial_data():
    try:
        cw = [221, 165, 3, 0, 255, 253, 119]
        logging.info("ask for basic Data")
        response = receive_data(cw)

        if len(response) > 0:
            parse_basicdata(response)

        cw = [221, 165, 4, 0, 255, 252, 119]
        logging.info("ask for Cell Data")
        response = receive_data(cw)

        if len(response) > 0:
            parse_cellinfo(response)

        cw = [0xDD, 0xA5, 0x05, 0x00, 0xFF, 0xFB, 0x77]
        logging.info("ask for bms info")

        response = receive_data(cw)

        if len(response) > 0:
            parse_bmsinfo(response)

        if args.victron:
            gobject.timeout_add(5000, handle_serial_data)

    except KeyboardInterrupt:
        if not args.victron:
            raise
    except:
        raise


if args.victron:
    gobject.timeout_add(1000, handle_serial_data)
    mainloop = gobject.MainLoop()
    mainloop.run()
else:

    while True:
        handle_serial_data()
        if args.json:
            print(json.dumps(BMS_STATUS, indent=4))
        if args.interval < 0:
            sys.exit(0)
        time.sleep(args.interval)
