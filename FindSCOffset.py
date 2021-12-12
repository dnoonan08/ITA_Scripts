from urllib.request import urlopen
import time

URL='https://www-bd.fnal.gov/notifyservlet/www'

response = urlopen(URL).read()
_time = float(str(response).split('SC time</a> = ')[1].split(' / ')[0])
systime=time.time()%60
print(f'SC time={_time}')
print(f'sys time={systime}')
print()
print(f'Offset={round(systime-_time)}')
