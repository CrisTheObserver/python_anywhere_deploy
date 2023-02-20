import parselmouth 
from parselmouth import praat
import numpy as np
import csv
from datetime import datetime
from datetime import timedelta

def audio_analysis(path, audio_name,timestamp=datetime.today()-timedelta(hours=2)):
    sound = parselmouth.Sound(path)
    f0min=75
    f0max=300
    pointProcess = praat.call(sound, "To PointProcess (periodic, cc)", f0min, f0max)

    formants = praat.call(sound, "To Formant (burg)", 0.0025, 5, 5000, 0.025, 50)

    numPoints = praat.call(pointProcess, "Get number of points")
    f1_list = []
    f2_list = []
    f3_list = []
    f4_list = []
    for point in range(0, numPoints):
        point += 1
        t = praat.call(pointProcess, "Get time from index", point)
        f1 = praat.call(formants, "Get value at time", 1, t, 'Hertz', 'Linear')
        f2 = praat.call(formants, "Get value at time", 2, t, 'Hertz', 'Linear')
        f3 = praat.call(formants, "Get value at time", 3, t, 'Hertz', 'Linear')
        f4 = praat.call(formants, "Get value at time", 4, t, 'Hertz', 'Linear')
        f1_list.append(f1)
        f2_list.append(f2)
        f3_list.append(f3)
        f4_list.append(f4)
    
    n_f1 = np.array(f1_list)
    n_f2 = np.array(f2_list)
    n_f3 = np.array(f3_list)
    n_f4 = np.array(f4_list)
    pitch = praat.call(sound, "To Pitch", 0.0, f0min, f0max)
    F0 = praat.call(pitch, "Get mean", 0, 0, 'Hertz')
    harmonicity = praat.call(sound, "To Harmonicity (cc)", 0.01, f0min, 0.1, 1.0)
    hnr = praat.call(harmonicity, "Get mean", 0, 0)

    pointProcess = praat.call(sound, "To PointProcess (periodic, cc)", f0min, f0max)
    localJitter = praat.call(pointProcess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    localabsoluteJitter = praat.call(pointProcess, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
    rapJitter = praat.call(pointProcess, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
    ppq5Jitter = praat.call(pointProcess, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
    ddpJitter = praat.call(pointProcess, "Get jitter (ddp)", 0, 0, 0.0001, 0.02, 1.3)
    localShimmer =  praat.call([sound, pointProcess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    localdbShimmer = praat.call([sound, pointProcess], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq3Shimmer = praat.call([sound, pointProcess], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    aqpq5Shimmer = praat.call([sound, pointProcess], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq11Shimmer =  praat.call([sound, pointProcess], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    ddaShimmer = praat.call([sound, pointProcess], "Get shimmer (dda)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    return {
        "name": audio_name,
        "timestamp":timestamp.strftime('%Y-%m-%d %H:%M'),
        "date":datetime.today().strftime('%Y-%m-%d %H:%M'),
        "f0": round(F0, 1),
        "f1": round(np.nanmean(n_f1), 1),
        "f2": round(np.nanmean(n_f2), 1),
        "f3": round(np.nanmean(n_f3), 1),
        "f4": round(np.nanmean(n_f4), 1),
        "Intensity": round(sound.get_intensity(), 2),
        "HNR": round(hnr, 2),
        "localJitter": round(localJitter,6),
        "localabsoluteJitter": round(localabsoluteJitter,6),
        "rapJitter": round(rapJitter,6),
        "ppq5Jitter": round(ppq5Jitter,6),
        "ddpJitter": round(ddpJitter,6),
        "localShimmer": round(localShimmer,6),
        "localdbShimmer": round(localdbShimmer,6),
        "apq3Shimmer": round(apq3Shimmer,6),
        "aqpq5Shimmer": round(aqpq5Shimmer,6),
        "apq11Shimmer": round(apq11Shimmer,6),
        "ddaShimmer": round(ddaShimmer,6)
        }

#This function receives a dictionary and write its information in the specified CSV file
def write_csv(new_data, username, filename, id_audio=-1):
    with open(filename, 'a', newline='') as csvfile:
        historical_writer = csv.writer(csvfile)
        #if we're writing the Historical CSV, we manually add the username field
        if filename == 'historical.csv':
            new_row = [username,id_audio]
        else:
            new_row = [id_audio]
        
        for key in new_data:
            new_row += [new_data[key]]
        historical_writer.writerow(new_row)
        csvfile.close()