from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django.core.files.storage import default_storage

import parselmouth 
from parselmouth import praat
import numpy as np
import os
import csv
import pandas as pd
from datetime import datetime
import plotly.express as px
from plotly.offline import plot

def audio_analysis(path, audio_name):
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
def write_csv(new_data, username, filename):
    with open(filename, 'a', newline='') as csvfile:
        historical_writer = csv.writer(csvfile)
        #if we're writing the Historical CSV, we manually add the username field
        if filename == 'historical.csv':
            new_row = [username]
        else:
            new_row = []
        
        for key in new_data:
            new_row += [new_data[key]]
        historical_writer.writerow(new_row)

def upload_audio_view(request):
    if request.method == 'GET':
        #With this we render the page with an undetermined number of optional audio file inputs
        return render(request,"upload_audio.html",{
            "title":"Subir archivos",
            "range":range(2,6)})

    if request.method == 'POST':
        username = request.POST['username']

        #Checking if a user is uploading for the first time (to create folder and CSV file) 
        new_user = not os.path.isdir(username)

        #Saving and analyzing the received audios (the directory is created here in case we have a new user)
        audio_list = request.FILES.getlist('audio')
        for audio in audio_list:
            audio_name = default_storage.save(username+'/'+audio.name, audio)
            res = audio_analysis(audio_name, audio.name)

            #Creating CSV file in case we have a new user
            if new_user:
                with open(username+'/audio_list.csv', 'w', newline='') as csvfile:
                    fieldnames = ["Nombre archivo","Fecha de subida", "F0","F1","F2","F3","F4","Intensidad","HNR","Local Jitter","Local Absolute Jitter", "Rap Jitter", "ppq5 Jitter","ddp Jitter","Local Shimmer","Local db Shimmer","apq3 Shimmer","aqpq5 Shimmer","apq11 Shimmer","dda Shimmer"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    new_user = False
            
            #Writing the data on CSV files
            write_csv(res, username, username+"/audio_list.csv")
            write_csv(res, username, "historical.csv")

        #Displays a table with all the audios uploaded by this user (including previously uploaded ones in case they exist)
        return HttpResponseRedirect('/show_audio/?username='+username)

def show_audio_view(request):
    username = request.GET["username"]
    #Reads the CSV and puts its information in an array
    with open(username+'/audio_list.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        csv_list = []
        for row in csvreader:
            csv_list += [row]
    #We render the page with the information we got
    return render(request,"table_display.html", {
        "title":"Audios de {0}".format(username),
        "args":csv_list[0],
        "audios":csv_list[1:],
        "filename":username+'/audio_list.csv'})

def historical_csv_view(request):
    #Reads the CSV and puts its information in an array
    with open('historical.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        csv_list = []
        for row in csvreader:
            csv_list += [row]
    #We render the page with the information we got
    return render(request,"table_display.html", {
        "title":"CSV histórico",
        "args":csv_list[0],
        "audios":csv_list[1:],
        "filename":"historical.csv"})
    

def download_file(request):
    filename = request.GET["filename"]
    #This gives us the path without the extension
    path = filename[:len(filename)-4]

    #We create an Excel file from our CSV file and save it alongside it
    read_file = pd.read_csv(filename, delimiter=",")
    new_file = pd.ExcelWriter(path+".xlsx")
    read_file.to_excel(new_file, index = False)
    new_file.save()

    #With this we trigger the file download
    with open(path+".xlsx", 'rb') as xlsx_file:
        response = HttpResponse(xlsx_file, content_type='application/vnd.openxmlformatsofficedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(path+".xlsx")
        return response

def hourly_graph_view(request):
    #Renders the selector after selecting graph type
    return render(request, "graph.html",{
        "title":"Selección de coeficiente",
        "format":"hourly",
        "args":["F0","F1","F2","F3","F4","Intensidad","HNR","Local Jitter","Local Absolute Jitter", "Rap Jitter", "ppq5 Jitter","ddp Jitter","Local Shimmer","Local db Shimmer","apq3 Shimmer","aqpq5 Shimmer","apq11 Shimmer","dda Shimmer"]
    })

def historical_graph_view(request):
    #Renders the selector after selecting graph type
    return render(request, "graph.html",{
        "title":"Selección de coeficiente",
        "format":"historical",
        "args":["F0","F1","F2","F3","F4","Intensidad","HNR","Local Jitter","Local Absolute Jitter", "Rap Jitter", "ppq5 Jitter","ddp Jitter","Local Shimmer","Local db Shimmer","apq3 Shimmer","aqpq5 Shimmer","apq11 Shimmer","dda Shimmer"]
    })

def display_hourly_graph_view(request):
    #This index that represents the value we have to display
    index = request.GET["index"]
    with open('historical.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        #Here we'll store the data that we need for the graph (username, date and the value that we want to show)
        user_list = []
        date_list = []
        arg_list = []
        for row in csvreader:
            user_list.append(row[0])
            date_list.append(row[2])
            #To get the desired value, we have to add 3 to the index received (the first 2 rows are for username, filename and date)
            arg_list.append(row[int(index)+3])
        #Since we want to show only based on the hour, we set all dates to the same year, month and day, so that hour and minutes are the only difference (the date was picked arbitrarily)
        #The data in the CSV is stored as strings, so we change it to the correct type
        date_list[1:]=[datetime.strptime(x, '%Y-%m-%d %H:%M').replace(year=2010,month=1,day=1) for x in date_list[1:]]
        arg_list[1:]=[float(x) for x in arg_list[1:]]

        #The first element of each list is the label, and the rest are the values
        df = pd.DataFrame(data={user_list[0]:user_list[1:],date_list[0]:date_list[1:],arg_list[0]:arg_list[1:]})
        fig = px.scatter(df, x=date_list[0], y=arg_list[0], color=user_list[0], template='plotly_dark')
        #If we don't change the format, it'll show that all files were uploaded on the same day, which is not ideal
        fig.update_xaxes(tickformat="%H:%M")
        div = plot(fig, auto_open=False, output_type='div')
    return render(request,"display_graph.html", {
        "title":"Análisis de {0} por hora del día".format(arg_list[0]),
        "graph":div})

def display_historical_graph_view(request):
    #This index that represents the value we have to display
    index = request.GET["index"]

    with open('historical.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        #Here we'll store the data that we need for the graph (username, date and the value that we want to show)
        user_list = []
        date_list = []
        arg_list = []
        for row in csvreader:
            user_list.append(row[0])
            date_list.append(row[2])
            #To get the desired value, we have to add 3 to the index received (the first 2 rows are for username, filename and date)
            arg_list.append(row[int(index)+3])
        #The data in the CSV is stored as strings, so we change it to the correct type
        date_list[1:]=[datetime.strptime(x, '%Y-%m-%d %H:%M') for x in date_list[1:]]
        arg_list[1:]=[float(x) for x in arg_list[1:]]

        #The first element of each list is the label, and the rest are the values
        df = pd.DataFrame(data={user_list[0]:user_list[1:],date_list[0]:date_list[1:],arg_list[0]:arg_list[1:]})
        fig = px.scatter(df, x=date_list[0], y=arg_list[0], color=user_list[0], template='plotly_dark')
        div = plot(fig, auto_open=False, output_type='div')
    return render(request,"display_graph.html", {
        "title":"Análisis histórico de {0}".format(arg_list[0]),
        "graph":div})
