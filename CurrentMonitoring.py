from AgilentPowerSupply import AgilentSupply
import logging
import time
import datetime
agilent=AgilentSupply()

logging.basicConfig(filename=f'logs/currentMonitoring_{datetime.datetime.now().strftime("%m_%d_%Y")}.log',
                    level=logging.INFO,
                    format='%(message)s',
                    )

logging.info(f'#{agilent.id()[:-1]}')
agilent.setLimits(v1=12,c1=1,
                  v2=1.2,c2=0.6)
v1,c1,v2,c2=agilent.readLimits()
logging.info(f'#LIMITS: {v1}, {v2} CURRENTS: {c1}, {c2}')

try:
    while True:
        v1,c1,v2,c2=agilent.read()
        logging.info(f'{datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")},{v1},{c1},{v2},{c2}')
        time.sleep(15)
except KeyboardInterrupt:
    print('exiting')
