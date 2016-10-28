#!/usr/bin/env python
###############################################################################
# icsp_flash.py                                                               #
#                                                                             #
#    Python script to interact with a Raspberry Pi wearing a PiProg HAT to    #
#    easily flash a program to a microcontroller using avrdude.               #
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
import os
import time


### Settings ###

# Path to avrdude. You need a version of avrdude with the 'linuxgpio' programmer.
# See http://ozzmaker.com/program-avr-using-raspberry-pi-gpio/
# Configure the linuxgpio programmer pinout in your avrdude.conf as follows:
#   reset = 12;
#   sck = 11;
#   mosi = 10;
#   miso = 9;
# maybe use linuxspi?
# http://www.instructables.com/id/Programming-the-ATtiny85-from-Raspberry-Pi/step4/Program-the-ATtiny85/
AVRDUDE_PATH = "/usr/bin/avrdude"

# Baud rate to use while programming the MCU. Leave blank for the default.
BAUD_RATE = ""

#avrdude -P comport -b 19200 -c avrisp -p m328p -v -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m
#avrdude -P comport -b 19200 -c avrisp -p m328p -v -e -U flash:w:hexfilename.hex -U lock:w:0x0F:m

# Type of MCU being flashed. See avrdude(4) for the -p option for more information.
PART_NUMBER = "m328p"

# Path to binary hex file to be flashed to the MCU. Popular arduino bootloaders can be found at:
# https://github.com/arduino/Arduino/tree/master/hardware/arduino/avr/bootloaders
HEX_FILE = "/path/to/eeprom.eep"

# MCU fuse bits to set. Double check these are correct for your chip!!
# A useful tool for finding fuse values: http://www.engbedded.com/fusecalc
FUSE_LOW = "0xFF"
FUSE_HIGH = "0xDA"
FUSE_EXTENDED = "0x05"

# leave blank for no lock bits
LOCK_BITS = "0x0F"





### main code ###

PIN_LED_GREEN = 33
PIN_LED_RED = 35
PIN_BUTTON = 37

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(PIN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_LED_GREEN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)


def main():
    print("icsp flasher running - press button to flash mcu!")
    try:
        while True:
            GPIO.output(PIN_LED_GREEN, GPIO.HIGH)
            if GPIO.input(PIN_BUTTON) == GPIO.LOW:
                print("flashing mcu... ")
                GPIO.output(PIN_LED_GREEN, GPIO.LOW)
                flash_mcu()
                print("   DONE!")
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        print("Exiting.")
        exit(0)

def blink_led(pin, times=1, delay=0.5):
    for i in range(times):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(delay)


def flash_mcu():
    GPIO.output(PIN_LED_RED, GPIO.HIGH)

    if not os.path.exists(HEX_FILE):
        print("hex file "+HEX_FILE+" does not exist!")
        blink_led(PIN_LED_RED, 3, 0.6)
    else:
        FNULL = open(os.devnull, 'w')

        result = subprocess.call(avrdude_fuse_params(), stdout=FNULL, stderr=subprocess.STDOUT)
        if result != 0:
            print("error setting mcu fuses")
            blink_led(PIN_LED_RED, 3, 0.5)
            return

        result = subprocess.call(avrdude_flash_params(), stdout=FNULL, stderr=subprocess.STDOUT)

        GPIO.output(PIN_LED_GREEN, GPIO.LOW)
        GPIO.output(PIN_LED_RED, GPIO.LOW)

        if result == 0:
            print("mcu flash successful")
            blink_led(PIN_LED_GREEN, 3, 0.2)
        else:
            print("error flashing mcu")
            blink_led(PIN_LED_RED, 3, 0.5)


def avrdude_fuse_params():
    params = [AVRDUDE_PATH,"-c","linuxgpio","-p",PART_NUMBER,
            "-U","efuse:w:"+FUSE_EXTENDED+":m",
            "-U","hfuse:w:"+FUSE_HIGH+":m",
            "-U","lfuse:w:"+FUSE_LOW+":m"]
    if BAUD_RATE != "":
        params.extend(["-b",BAUD_RATE])
    return params


def avrdude_flash_params():
    params = [AVRDUDE_PATH,"-c","linuxgpio","-p",PART_NUMBER,"-U","flash:w:"+HEX_FILE]
    if LOCK_BITS != "":
        params.extend(["-U","lock:w:"+LOCK_BITS+":m"])
    if BAUD_RATE != "":
        params.extend(["-b",BAUD_RATE])
    return params


if __name__ == '__main__':
    sys.exit(main())
