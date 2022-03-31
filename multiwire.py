from urllib.request import urlopen
import numpy as np
import pandas as pd

encoding = 'utf-8'



def get_multiwire_data(T1,T2,dev='UMW5DS'):
    URL=f'https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=logger_get/start={T1}/end={T2}/node=QRAY1+E:{dev}'
    response = urlopen(URL).read()
    lines = str(response)[2:-1].split('\\n')

    currentTime=None
    thisdata=[]
    timestamps=[]
    data_x=[]
    data_y=[]
    for l in lines[:-1]:
        thisDate, thisTime, thisVal = l.split()
        t=thisDate+' '+thisTime
        if not t==currentTime:
            if not currentTime is None:
                if len(thisdata)==216: #add condition, since sometimes not all data is found
                    thisdata_=np.array(thisdata[104:-16]).reshape(2,48)*-1
                    data_x.append(thisdata_[0])
                    data_y.append(thisdata_[1])
                    timestamps.append(currentTime)
            thisdata=[]
            currentTime=t

        thisdata.append(float(thisVal))

    #data[currentTime] = np.array(thisdata[104:-16]).reshape(2,48)*-1
    thisdata_=np.array(thisdata[104:-16]).reshape(2,48)*-1
    data_x.append(thisdata_[0])
    data_y.append(thisdata_[1])
    timestamps.append(currentTime)

    df=pd.DataFrame({'X':data_x,'Y':data_y},index=timestamps)
    return df

if __name__=="__main__":
    T1='10-Mar-2022-00:00:00'
    T2='10-Mar-2022-11:59:59'
    dev='UMW5DS' ##multiwire MW109B in ACNET

    df = get_multiwire_data(T1,T2)
