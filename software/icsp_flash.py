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
import signal
import os
import time


### Settings ###

# Path to avrdude.
AVRDUDE_PATH = "/usr/bin/avrdude"

# Linux SPI dev. Make sure to enable SPI via raspi-config first.
SPI_DEV = "/dev/spidev0.0"

# Baud rate to use while programming the MCU.
BAUD_RATE = "250000"

# Type of MCU being flashed. See avrdude(4) for the -p option for more information.
PART_NUMBER = "m328p"

# Path to binary hex file to be flashed to the MCU. Popular arduino bootloaders can be found at:
# https://github.com/arduino/Arduino/tree/master/hardware/arduino/avr/bootloaders
HEX_FILE = "/path/to/program.hex"

# MCU fuse bits to set. Double check these are correct for your chip!!
# A useful tool for finding fuse values: http://www.engbedded.com/fusecalc
FUSE_LOW = "0xE2"
FUSE_HIGH = "0xDE"
FUSE_EXTENDED = "0x05"

# leave blank for no lock bits
LOCK_BITS = ""




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
    signal.signal(signal.SIGINT, handle_sigint)

    print("icsp flasher running - press button to flash mcu!")

    while True:
        GPIO.output(PIN_LED_GREEN, GPIO.HIGH)
        if GPIO.input(PIN_BUTTON) == GPIO.LOW:
            print("flashing mcu... ")
            GPIO.output(PIN_LED_GREEN, GPIO.LOW)
            flash_mcu()
            print("   DONE!")


def handle_sigint(signal, frame):
    GPIO.cleanup()
    print("Exiting.")
    sys.exit(0)


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
            return result
        else:
            print("fuses set")

        time.sleep(2)

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
    params = [AVRDUDE_PATH,"-c","linuxspi","-P",SPI_DEV,"-p",PART_NUMBER,
            "-U","efuse:w:"+FUSE_EXTENDED+":m",
            "-U","hfuse:w:"+FUSE_HIGH+":m",
            "-U","lfuse:w:"+FUSE_LOW+":m"]
    if BAUD_RATE != "":
        params.extend(["-b",BAUD_RATE])
    return params


def avrdude_flash_params():
    params = [AVRDUDE_PATH,"-c","linuxspi","-P",SPI_DEV,"-p",PART_NUMBER,"-U","flash:w:"+HEX_FILE]
    if LOCK_BITS != "":
        params.extend(["-U","lock:w:"+LOCK_BITS+":m"])
    if BAUD_RATE != "":
        params.extend(["-b",BAUD_RATE])
    return params


if __name__ == '__main__':
    sys.exit(main())
