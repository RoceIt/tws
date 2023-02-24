#!/usr/bin/python3

from subprocess import Popen
import mypy

def main():
    open('/home/rolcam/TraderZone/tmp/aex5s.data', 'w').close()
    Popen('R --vanilla -f /home/rolcam/TraderZone/bin/R_scripts/getSNPintradayDataFromIB.R',
          shell=True)

main()
