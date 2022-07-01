import argparse
from urllib.request import urlopen
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
from time import sleep

#For development purposes, a limit on rows to deal with
quickrun = 10

def checkdigit(s):
    """ Returns True is string is a number. """
    return s.lstrip('-').replace('.','',1).isdigit()

# Using http interface.
# Return: DataFrame with columns 'timestamp', 'proton count', and 'Integrated Protons'
def getITAdata(T1, T2, device='E:UTR112', logger='MTA', testrange=-1):
    encoding = 'utf-8'
    URL = 'http://www-bd.fnal.gov/cgi-bin/acl.pl?acl=logger_get/start='+str(T1)+'/end='+str(T2)+'/node='+logger+'+'+str(device)
    if debug: print (URL)
    response = urlopen(URL).read()
    lines = str(response)[2:-1].split('\\n')

    if debug: print (lines)
    integrate = 0.0
    entryUnsort = []
    for line in lines:
        #line = str(line, encoding)
        fields = line.split()
        if len(fields) == 3:
            entryUnsort.append(fields)
    #close loop over lines
    entrySort = sorted(entryUnsort)
    # print (str(len(entrySort))+' total measurements found.')
    entrynum = 0
    i_entry = 0

    values = []
    timestamps = []
    for entry in entrySort:
        i_entry += 1
        if testrange>0 and i_entry>testrange: break
        # # Why is the very last one a byte string? And why can't we just test for that data type? Sigh.
        # if i_entry >= len(entrySort):
        #     print('HERE')
        #     break

        if debug: print(entry)
        if not len(entry) == 3:
            print('HERE2')
            continue
        thisDate, thisTime, theseE12 = entry
        if not checkdigit(theseE12):
            print('HERE3')
            continue # Sometimes it's '*****' and not a number.
        else:
            protoncount = abs(float(theseE12))*1e12
        # Need to check minimum time between measurements?  50 seconds?
        values.append(protoncount)
        ts_string = thisDate+' '+thisTime
        timestamps.append(pd.to_datetime(ts_string))
        integrate += protoncount

    #close loop over entries
    # Add lists to dataframe, and convert the timestamps to epoch seconds (not nanoseconds)
    df = pd.DataFrame({'timestamp':timestamps, 'proton count':values})
#    df['timestamp'] = df['timestamp'].astype('int64')//1.0e9

    # Add cumulative sum to the dataframe, and return
    df.sort_values('timestamp', inplace=True)
    df['Integrated Protons'] = df['proton count'].cumsum()
    return integrate, df


def normalRun(cmdT1, cmdT2, debug, goal, extrapolate, extrapo):
    ###########################################################################
    # Main body of the script
    ###########################################################################
    total, df  = getITAdata(cmdT1, cmdT2)

    print('Integrated protons at ITA:')
    print (cmdT1+" to "+cmdT2 +': ' + '{0:.2e}'.format(total),)
    if goal>0:
        goal_str = str(goal)
        goal_pct_str = '{0:.2f}'.format((total/goal)*100)
        print (' \t' + goal_pct_str + '% of goal '+goal_str+'.')
    else: print ('.')

    if debug: print (df)
    # Title string for plot
    if total==0:
        return df
    title = 'ITA Proton Accumulation: '+'{0:.2e}'.format(df['Integrated Protons'].iloc[-1])
    if goal>0:
        df['Goal'] = goal
        title += '\n('+goal_pct_str+'% of '+goal_str+')'

    # Negative arguments to '-x' switch return the whole shebang.
    if extrapo < 0:
        extrapo = df['proton count'].size

    # The extrapolation in its ugly details
    extratext = ''
    if extrapolate:
        shortdf = df.tail(extrapo)

        # Get the mean proton count
        protoncounts = shortdf['proton count'].dropna().astype(float)
        count_avg = protoncounts.mean()

        shotssofar = len(protoncounts)+1
        print ('Shots so far:'+ str(shotssofar))

        # Set outliers more than 10% above or below mean to NaN
        #protoncounts  = protoncounts.where( protoncounts >= 0.9*count_avg )
        #protoncounts  = protoncounts.where( protoncounts <= 1.1*count_avg )
        protoncounts.dropna(inplace=True) #...and drop NaN


        # Fit a guassian to +/- 10% of the mean proton count
        from scipy.stats import norm
        mean_counts,sigm_counts=norm.fit(protoncounts)
        print ('Count size range (excluding outliers): {0:.4e} +/- {1:.4e}'.format(mean_counts, sigm_counts))
        count_lo = mean_counts - sigm_counts
        count_hi = mean_counts + sigm_counts

        # We want to know how much is left still to go.
        protons_sofar = float(shortdf['Integrated Protons'].iloc[-1])
        print ('Accumulated POT: {0:.4e}'.format(protons_sofar))
        protons_lefttogo = goal - protons_sofar
        print ('Remaining POT: {0:.4e}\n'.format(protons_lefttogo))
        shotsleft_avg = protons_lefttogo/mean_counts
        shotsleft_lo = protons_lefttogo/count_hi
        shotsleft_hi = protons_lefttogo/count_lo
        print ('Remaining beam pulse count: Between {0:.4e} and {1:.4e}'.format(shotsleft_lo, shotsleft_hi))

        # There is a mean interval between beam pulses, and some std about that mean.
        epochSecs = shortdf['timestamp']
        first_timestamp = shortdf['timestamp'][0]
        last_timestamp  = shortdf['timestamp'].iloc[-1]
        SecondsSoFar = last_timestamp - first_timestamp
        print ('Elapsed time in seconds since first beam: '+str(SecondsSoFar))
        print ('   Approx. time-averaged beam rate: {0:.3e} protons per second.'.format(protons_sofar / SecondsSoFar))

        crude_interval_avg = SecondsSoFar / float(shotssofar)
        print ('   Approx. time-averaged shot interval {0:.3e} s'.format(crude_interval_avg))
        # How long will it take?
        last = pd.Timestamp(last_timestamp, unit='s')
        roughguess = last + pd.Timedelta(seconds = crude_interval_avg * shotsleft_avg)
        print ('\n  Rough guess is ' + str(roughguess))

        # Take row-to-row diffs, and drop row 0 (it will be nonsense).
        timediffs = epochSecs.diff().iloc[1:]
        if debug: print('Fetched a few datetimes: '+str(len(epochSecs)))

        if debug: print ('timediffs min and max before trimming outliers: ',str(timediffs.min())+' and '+str(timediffs.max()))

        # Trim away outliers more than 10% from the mode
        import statistics as stats
        interval_mode = stats.mode(timediffs)
        interval_mean = stats.mean(timediffs)
        if debug: print ('Mode interval: '+str(interval_mode))
        if debug: print ('Mean interval: '+str(interval_mean))
        #timediffs = timediffs.where( timediffs >= 0.9*interval_mode)
        #timediffs = timediffs.where( timediffs <= 1.1*interval_mode)
        timediffs.dropna(inplace=True) #...and drop NaN
        if debug: print ('    Inliner TimeDiffs: ',timediffs.size)

        mean_interval, sigm_interval = norm.fit(timediffs)
        # Fitting may fail, returning nan values. If so, fall back on non-fitting stats:
        if math.isnan(mean_interval):
            mean_interval = stats.mean(timediffs.values)
        if math.isnan(sigm_interval):
            sigm_interval = stats.rms(timediffs.values)

        interval_lo  = mean_interval - sigm_interval
        interval_hi  = mean_interval + sigm_interval
        interval_avg = mean_interval
        #print ('Within 10\% of mode, fitted interval from shot to shot 1-sigma range: {0:.3e} to {1:.3e} s'.format(interval_lo, interval_hi))
        #print ('Interval Mu and sigma:  '+str(mean_interval)+' +/- '+str(sigm_interval)+' s')

        bestguess    = last + pd.Timedelta(seconds = interval_avg * shotsleft_avg)
        bestguess_lo = last + pd.Timedelta(seconds = interval_lo  * shotsleft_lo )
        bestguess_hi = last + pd.Timedelta(seconds = interval_hi  * shotsleft_hi )

        #print ('\n  Best guess is ' + str(bestguess))
        #print ('Early side: '+ str(bestguess_lo))
        #print ('Later side: '+ str(bestguess_hi))

        extratext  = 'Remaining POT: {0:.4e}\n     ---\n'.format(protons_lefttogo)
        extratext += 'Typical pulse size [ppp]:\n{0:.2e} +/- {1:.2e}\n     ---\n'.format(mean_counts, sigm_counts)
        extratext += 'Remaining beam pulse count:\nbetween {0:.2e} and {1:.2e}\n     ---\n'.format(shotsleft_lo, shotsleft_hi)
        #extratext += 'Cycle time [s]:\n{0:.2f} +/- {1:.2f}\n     ---\n'.format(mean_interval,sigm_interval)
        extratext += 'Estimated completion time:\n'+str(roughguess.round('s'))+'\n'
        #extratext += '\nReasonable window based on \nobserved fluctations:\n'+str(bestguess_lo.round('s'))+'\n to \n'+str(bestguess_hi.round('s'))

    #Need to drop the original measurements for easy plotting?
    measurements = df['proton count'].to_list()
#    df.drop(columns=['proton count'], axis=0, inplace=True)
    if debug: print (df.columns.values)

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    if debug: print (df)

    if options.makePlot:
        # Make the plot, returning the Axes object
        plt.figure(figsize=(9.0,6.0))
        ax = sns.lineplot(x='timestamp', y='value', hue='variable', data=pd.melt(df.drop(columns=['proton count'], axis=0), ['timestamp']))
        #ax2.plot(measurements)
        plt.title(title)
        plt.ticklabel_format(style='scientific', axis='y', useOffset=False, useMathText=True, scilimits=(0,0))
        plt.xticks(rotation=20)
        plt.xlabel('')
        plt.ylabel('Protons')
        plt.grid(True, which='both', axis='both')

        ax2 = ax.twinx()
        ax2.plot(df['timestamp'], measurements, color='black', alpha=0.5)
        #suppress zero suppression
        ax2.set_ylim(bottom=0.0)
        plt.ticklabel_format(style='scientific', axis='y', useOffset=False, useMathText=True, scilimits=(0,0))

        # Legend
        firsttimestamp = df['timestamp'].astype(str).iloc[0]
        laasttimestamp = df['timestamp'].astype(str).iloc[-1]
        firsttimestamp = str(pd.Timestamp(df['timestamp'].iloc[ 0], unit='s'))
        laasttimestamp = str(pd.Timestamp(df['timestamp'].iloc[-1], unit='s'))
        handles, labels = ax.get_legend_handles_labels()
        # manually define a new patch
        patch = mpatches.Patch(color='black', label='Per-shot E12', alpha=0.5)
        handles.append(patch)
        ax.legend(handles=handles,
                  title=firsttimestamp+'\n to \n'+laasttimestamp,
                  bbox_to_anchor=(1.45, 1.00),
                  loc='upper right')

        plt.tight_layout()
        plt.gcf().text(0.70, 0.1, extratext, fontsize=11)

        outfilename = 'AccumulatedITAprotons_withExtrapolation.png'
        plt.savefig(outfilename)
        print ('Saved output as '+outfilename)
    return df

if __name__=='__main__':
    ### Make a command-line argument parser
    parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
    ### Add options
    parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                         help="Turn on verbose debugging. (default: False)")
    parser.add_argument ('--T1', dest='T1', default='',
                         help='Start of integration window. DD-jan-YYYY-hh:mm:ss (default: Beginning of most recent Monday)')
    parser.add_argument ('--T2', dest='T2', default='',
                         help='End of integration window. DD-feb-YYYY-hh:mm:ss (default: now)')
    parser.add_argument ('--goal', dest='goal', default=0,
                         help='Integrated proton goal. Example: 1.0e18')
    parser.add_argument ('--extrapolate', '-x', dest='extrapo', default=-1,
                         help='If nonzero, x most recent measurements (<0 for all), to estimate when goal met.')
    parser.add_argument ('--quick', '-q', dest='quick', action="store_true", default =False,
                         help='Stop after '+str(quickrun)+' rows.')
    parser.add_argument ('--plot', dest='makePlot', action="store_true", default =False,
                         help='Run plotting step')
    parser.add_argument ('--fileName', dest='fileName', default =None,
                         help='File name to save data to')
    parser.add_argument ('--continuous', dest='continuousRun', action="store_true", default =False,
                         help='Run continuously, sleeping 60 seconds between')

    ### Get the options and argument values from the parser....

    options = parser.parse_args()

    if options.makePlot:
        import seaborn as sns
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

    ### ...and assign them to variables. (No declaration needed, just like bash!)
    debug     = options.debug
    cmdT1     = options.T1
    cmdT2     = options.T2
    quick     = options.quick
    extrapo   = int(options.extrapo)

    # Convert types if needed
    goal = float(options.goal)

    # Set the switch to extrapolate. Need both a goal and a count of data points to use.
    #if goal>0 and extrapo>0: extrapolate = True
    if goal>0: extrapolate = True
    else: extrapolate = False

    datetimeformat_str = '%d-%b-%Y-%H:%M:%S'
    now = pd.Timestamp.now()
    if cmdT2 == '':
        cmdT2 = now.strftime(datetimeformat_str)
        if debug: print (cmdT2)

    if cmdT1 == '':
        today = datetime.now().date()
        # Week begins Monday
        wkbegin = today - timedelta(days=(today.weekday()))
        cmdT1 = (wkbegin.strftime(datetimeformat_str))

    if debug: print ('Verbose debugging output on.')
    if debug and goal == 0: print ('No fluence goal stated')

    if options.continuousRun:
        first=True
        total=0
        while True:
            now = pd.Timestamp.now()
            cmdT2 = now.strftime(datetimeformat_str)
            total_, df  = getITAdata(cmdT1, cmdT2)
#            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if first:
                print(df)
                first=False
            else:
                N=len(df)
#                print(df.loc[N-1:N])
                print(df)
            cmdT1 = cmdT2
            total += total_
            goalFrac=""
            if goal>0:
                goalFrac=f' ({(total/goal)*100:.02f}% of goal)'
            print(f'Total protons delivered: {total:.04e}{goalFrac}')
            sleep(60)
    else:
        df = normalRun(cmdT1, cmdT2, debug, goal, extrapolate, extrapo)

    if options.fileName is not None:
        df.to_csv(options.fileName)
