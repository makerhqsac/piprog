#!/usr/bin/env python
###############################################################################
# hat_write.py                                                                #
#                                                                             #
#    Python script to interact with a Raspberry Pi wearing a PiProg HAT to    #
#    easily build a unique eeprom from a eepmake settings file and write      #
#    it to an eeprommmmmmmm.                                                  #
#                                                                             #
#    Specify the eeprom_settings.txt file as an argument to this script.      #
#    A new file of the same name with a .eep extension will be generated      #
#    and written to the eeprom.                                               #
#                                                                             #
#    For more information, see https://github.com/makerhqsac/piprog           #
#                                                                             #
#    Written By Mike Machado <mike@machadolab.com>                            #
#    Sponsored by MakerHQ - http://www.makerhq.org                            #
#                                                                             #
#    Licensed under the GPLv3 - https://www.gnu.org/licenses/gpl-3.0.txt      #
###############################################################################
import RPi.GPIO as GPIO
import subprocess
import sys
import signal
import os
import time


### Settings ###


# Type of EEPROM. Supported types: 24c32, 24c64, 24c128, 24c512, and 24c1024.
EEPROM_TYPE = "24c32"


# Path to the eepmake utility from the raspberrypi hats repo: https://github.com/raspberrypi/hats.
EEPMAKE_PATH = "/path/to/eepmake"



### main code ###

EEPROM_SETTINGS_FILE = sys.argv[1]

PIN_LED_GREEN = 33
PIN_LED_RED = 35
PIN_BUTTON = 37

I2C_DEV_PATH = "/sys/class/i2c-adapter/i2c-3"
I2C_DEV_NAME = "3-0050"
I2C_USE_BITBANG = True

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(PIN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_LED_GREEN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)


def main():
    if not os.path.exists(EEPROM_SETTINGS_FILE):
        print("Invalid settings file. Usage: " + sys.argv[0] + " <eeprom_settings.txt>")
        sys.exit(1)

    setup_i2c()
    signal.signal(signal.SIGINT, handle_sigint)

    print("eeprom writer running - press button to program eeprom!")

    while True:
        GPIO.output(PIN_LED_GREEN, GPIO.HIGH)
        if GPIO.input(PIN_BUTTON) == GPIO.LOW:
            print("writing eeprom... ")
            GPIO.output(PIN_LED_GREEN, GPIO.LOW)
            write_eeprom()
            print("   DONE!")


def handle_sigint(signal, frame):
    GPIO.cleanup()
    print("Exiting.")
    sys.exit(0)



def setup_i2c():
    if not subprocess.call(["modprobe", "i2c_dev"]) == 0:
        print("error loading i2c_dev kernel module")
        exit(1)
    if I2C_USE_BITBANG:
        if not subprocess.call(["dtoverlay", "i2c-gpio","i2c_gpio_sda=2","i2c_gpio_scl=3"]) == 0:
            print("error loading i2c-gpio dtoverlay. If the dtoverlay command is not found, please update to latest raspian")
            exit(1)
    if not subprocess.call(["modprobe","at24"]) == 0:
        print("error loading at24 kernel module")
        exit(1)
    if not os.path.exists(I2C_DEV_PATH+"/"+I2C_DEV_NAME):
        new_device = open(I2C_DEV_PATH+"/new_device", "w")
        new_device.write(EEPROM_TYPE+" 0x50\n")
        new_device.close()
    if not os.path.exists(I2C_DEV_PATH+"/"+I2C_DEV_NAME+"/eeprom"):
        print("eeprom does not exist on i2c device " + I2C_DEV_PATH+"/"+I2C_DEV_NAME)
        exit(1)


def blink_led(pin, times=1, delay=0.5):
    for i in range(times):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(delay)


def write_eeprom():
    GPIO.output(PIN_LED_RED, GPIO.HIGH)

    FNULL = open(os.devnull, 'w')

    eeprom_binary_file = EEPROM_SETTINGS_FILE + ".eep"
    subprocess.call([EEPMAKE_PATH, EEPROM_SETTINGS_FILE, eeprom_binary_file], stdout=FNULL, stderr=subprocess.STDOUT)

    if not os.path.exists(eeprom_binary_file):
        print("eeprom file " + eeprom_binary_file + " does not exist!")
        blink_led(PIN_LED_RED, 3, 0.6)
    else:
        result = subprocess.call(["dd", "if=" + EEPROM_SETTINGS_FILE, "of=" + I2C_DEV_PATH + "/" + I2C_DEV_NAME + "/eeprom"], stdout=FNULL, stderr=subprocess.STDOUT)

        GPIO.output(PIN_LED_GREEN, GPIO.LOW)
        GPIO.output(PIN_LED_RED, GPIO.LOW)

        if result == 0:
            print("eeprom write successful")
            blink_led(PIN_LED_GREEN, 3, 0.2)
        else:
            print("error writing eeprom")
            blink_led(PIN_LED_RED, 3, 0.5)


if __name__ == '__main__':
    sys.exit(main())
