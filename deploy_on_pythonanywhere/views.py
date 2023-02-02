from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.core.files.storage import default_storage

import parselmouth 
from parselmouth import praat

import numpy as np

def audio_analysis(audio_name):

    sound = parselmouth.Sound(audio_name)
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

    return [
            round(F0, 1),
            round(np.nanmean(n_f1), 1),
            round(np.nanmean(n_f2), 1),
            round(np.nanmean(n_f3), 1),
            round(np.nanmean(n_f4), 1),
            round(sound.get_intensity(), 2),
            round(hnr, 2),
            round(localJitter,6),
            round(localabsoluteJitter,6),
            round(rapJitter,6),
            round(ppq5Jitter,6),
            round(ddpJitter,6),
            round(localShimmer,6),
            round(localdbShimmer,6),
            round(apq3Shimmer,6),
            round(aqpq5Shimmer,6),
            round(apq11Shimmer,6),
            round(ddaShimmer,6)
            ]


def index_view(request):
    if request.method == 'GET': 
        return render(request,"index.html")

    if request.method == 'POST':
        audio = request.FILES['audio']
        try:
            audio2 = request.FILES['audio2']
            audio2_name = default_storage.save(audio2.name, audio2)
        except:
            audio2_name = ''
        audio_name = default_storage.save(audio.name, audio)

        return HttpResponseRedirect('/show_audio/?audio='+audio_name+'&audio2='+audio2_name)

def show_audio_view(request):
    audio_name = request.GET["audio"]
    res = audio_analysis(audio_name)

    audio2_name = request.GET["audio2"]
    res2 = []
    if audio2_name != '':
        res2 = audio_analysis(audio2_name)
    
    return render(request,"show_audio.html", {
        "name": audio_name,
        "name2": audio2_name,
        "args":[
            "f0",
            "f1",
            "f2",
            "f3",
            "f4",
            "I",
            "HNR",
            "localJitter",
            "localabsoluteJitter",
            "rapJitter",
            "ppq5Jitter",
            "ddpJitter",
            "localShimmer",
            "localdbShimmer",
            "apq3Shimmer",
            "aqpq5Shimmer",
            "apq11Shimmer",
            "ddaShimmer"],
        "vals":res,
        "vals2":res2})