#!/usr/bin/env python
import time
import os
import RPi.GPIO as GPIO
import OSC 
import threading

# launch pd-extended
os.system("pd-extended -nogui -noadc ./WindPi.pd &")
time.sleep(5)

# GPIO
GPIO.setmode(GPIO.BCM)
DEBUG = 1

# init OSC
localClient = OSC.OSCClient()
localClient.connect(('127.0.0.1', 9001))
msg = OSC.OSCMessage()

######
######
# Probleme dans le threading??? # 
######

#localOSCserver = OSC.ThreadingOSCServer(('127.0.0.1', 9002)) # used to receive, from pd, the number of the tts phrase to read

# define Text to Speech
#ph = ['','','','','']
#say = 'IFS=+;/usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols "http://translate.google.com/translate_tts?tl=fr&q=%s"'
#ph[0] = 'Assez glander, il est temps de retourner travailler'
#ph[1] = 'Attention, Jasonne te surveille'
#ph[2] = 'Tu es encore la?'
#ph[3] = 'Nespaire pas mentendre chanter en pluss'
#ph[4] = ' '	
#
#def ph_handler(addr, tag, stuff, source):
#	if addr=="/ph":
#		print stuff[0]
#		os.system(say % ph[stuff[0]] )
#		print say % ph[stuff[0]]
#
#localOSCserver.addMsgHandler("/ph", ph_handler)
#
#st =threading.Thread(target=localOSCserver.serve_forever)
#st.start()

######
######

#artministrator = OSC.OSCClient()	# envoi OSC pour test pd sur artministrator
#artministrator.connect(('192.168.2.103', 9001))

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False) # start clock low
        GPIO.output(cspin, False) # bring CS low

        commandout = adcnum
        commandout |= 0x18 # start bit + single-ended bit
        commandout <<= 3 # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1 # first bit is 'null' so drop it
        return adcout

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# 10k trim pot connected to adc #0
sensor_adc = 2;

last_read = 0 # this keeps track of the last sensor value
tolerance = 0 # to keep from being jittery we'll only change
                    # volume when the pot has moved more than 5 'counts'
avgrange = 50 # Quantity of values to avarage

msg.setAddress("/avgrange")
msg.append(avgrange)
localClient.send(msg)
#artministrator.send(msg)

try:
	while True:

		sum = 0
		for i in range(avgrange):
			sensor = readadc(sensor_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
			sum += sensor

		sensor_avg = sum/avgrange
		distance = sensor_avg * 1.6667 + 4      # * 0.8 * 2.54 
#	        print "distance:", distance
#		print "sensor value:", sensor_avg
	
   		# OSC -> Pd
		try:
			msg.setAddress("/distance1")
			msg.append(sensor_avg)
			localClient.send(msg)
#			artministrator.send(msg)
			msg.clearData()
		except:
#			print 'connection refused'
			pass		

		# hang out and do nothing
	        # time.sleep(0.1)
	
except KeyboardInterrupt:
	print "---"
	print "Closing WindPi"
	print "---"
	os.system("killall pd-extended")
	GPIO.cleanup()
	localOSCserver.close()
	st.join()
	print "---"
	print "See ya!"
	print "---"
