import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks

#Load the data. Insert the absolute file path to your data file here
data = pd.read_csv(r'C:\Users\krita\OneDrive\Desktop\C2\exams\2016-06\Temperatures\Temperatures\2016-06\2016-06\2016-06-02-00-31-12.log', delimiter=';', usecols=['Time', 'AM_SOC_FWD'], parse_dates=['Time'])

#Extract the data. Write the header of the column of data you wish to analyze inside
#the 'AM_SOC_FWD' of yaxis. Ensure that usecols in pd.read_csv above also has that header 
#in it. If the header of your time column is not 'Time', also substitute 'Time' with that 
#header. The columns are here turned to lists
time = data['Time']
yaxis = data['AM_SOC_FWD'].values

#Plot the original signal
plt.figure(figsize=(10, 5))
plt.plot(time, yaxis)
plt.xlabel('Time')
plt.ylabel('yaxis')
plt.title('Signal with Spikes')
plt.grid(True)

#Find all the indexes that are peaks in yaxis, and set them together in an organized list
upper_peaks, _ = find_peaks(yaxis)
lower_peaks, _ = find_peaks(-yaxis)
all_peaks = sorted(np.append(upper_peaks, lower_peaks))
#all_peaks = sorted(np.append(np.append([0], all_peaks), [len(yaxis)-1]))

#List of all the peaks in yaxis (the values, not the indexes)
all_y_peaks = yaxis[all_peaks]


threshold = 5
real_peaks=[]
peak_index = 0
first_round = True

#The Core Algorithm. First, a loop which finds and appends into real_peaks the indexes of yaxis which are
#peaks and either 1) there is a gap larger than threshold between the yaxis peak and the previous
#yaxis peak or 2) the yaxis peak continues in the same trajecteroy (upwards / downwards) as the previous two yaxis real_peaks. 
#It is important to note that all_peaks alternate between upper peaks and lower peaks, due to it being sorted. It
#is therefore known that if, for example, the next yaxis peak goes upwards in relation to the previous one,
#the previous one goes downwards in relation to the one before that. There are two lines after this while block which 
#can be un-commented to make this loop visually more clear...
while peak_index < len(all_peaks):

    if first_round:
        next_index = peak_index + 1
        current_peak_index = peak_index
        real_peaks.append(all_peaks[current_peak_index])
        while next_index < len(all_peaks) and abs(all_y_peaks[next_index] - all_y_peaks[current_peak_index]) < threshold:
            next_index+=1
            peak_index+=1
        
        first_round = False
        peak_index += 1
        continue


    real_peaks.append(all_peaks[peak_index])
    
    #Notice that every peak_index += 1 in this if block signifies skipping over that index, as we always
    #peak_index += 1 at the end of this while loop
    if peak_index < len(all_y_peaks)-1:
        if abs(all_y_peaks[peak_index]-all_y_peaks[peak_index+1])<threshold:
            next_index = peak_index+2
            current_peak_index = peak_index
            peak_index += 1
            if all_y_peaks[current_peak_index+1] > all_y_peaks[current_peak_index]:
                while(next_index <= len(all_y_peaks)-1 and 0 <= (all_y_peaks[next_index]-all_y_peaks[current_peak_index]) < threshold):
                    peak_index+=1
                    next_index+=1
            else:
                while(next_index <= len(all_y_peaks)-1 and 0 <= (all_y_peaks[current_peak_index]-all_y_peaks[next_index]) < threshold):
                    peak_index+=1
                    next_index+=1
        
            
    peak_index += 1

real_peaks = np.array(real_peaks)
###Un-comment these next two line if you wish to see how the peaks of the graph are without
###refining the peaks. This should illustrate why we refine soc_peaks after
#plt.plot(time[real_peaks], yaxis[real_peaks], "x", c="blue")
#plt.plot(time[real_peaks], yaxis[real_peaks], c="red")

#List of all the real_peaks in yaxis (the values, not the indexes)
soc_peaks = yaxis[real_peaks]

#...Second, we refine soc_peaks by finding its indexes that are peaks and setting them together in
#an organized list. After that...
upper_peaks, _ = find_peaks(soc_peaks)
lower_peaks, _ = find_peaks(-soc_peaks)
all_peaks = sorted(np.append(upper_peaks,lower_peaks))
all_peaks = sorted(np.append(np.append([0], all_peaks), [len(soc_peaks)-1]))

#...one can plot the soc_peaks' peaks and spikes and notice that every gap that is larger than threshold
#between the yaxis peaks has been found and plotted and...
plt.plot(time[real_peaks[all_peaks]], soc_peaks[all_peaks], "x", c="green")
plt.plot(time[real_peaks[all_peaks]], soc_peaks[all_peaks], c="orange")

#...printed out to make clear which peaks the spikes fall between
for i in range(len(all_peaks)):
    if i != len(all_peaks) - 1:
        peak_index_1 = all_peaks[i]
        peak_index_2 = all_peaks[i + 1]
        print(f"From {time[real_peaks[peak_index_1]]} to {time[real_peaks[peak_index_2]]} ---- Range of {abs(soc_peaks[peak_index_2] - soc_peaks[peak_index_1])}")
        print()

plt.show()