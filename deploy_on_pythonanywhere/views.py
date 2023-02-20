from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django.core.files.storage import default_storage

import deploy_on_pythonanywhere.scripts as scripts
import os
import csv
import pandas as pd
from datetime import datetime
import plotly.express as px
from plotly.offline import plot
import urllib.request, json

def update_csv_view(request):
    if request.method == 'GET':
        #With this we render the page with an undetermined number of optional audio file inputs
        return render(request,"update_csv.html",{
            "title":"Actualizar CSV histórico"})

    if request.method == 'POST':
        with urllib.request.urlopen("https://rtdf.pythonanywhere.com/api/audios/") as url:
            audio_list = json.load(url)

        with open('historical.csv') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)
            #Here we'll store the data that we need for the graph (username, date and the value that we want to show)
            id_list = []
            for row in csvreader:
                id_list.append(int(row[1]))
            csvfile.close()

        for audio_data in audio_list:
            id_audio = audio_data['id_audio']
            if id_audio not in id_list:
                #Getting data from the JSON
                username = str(audio_data['idusuario'])
                timestamp = datetime.strptime(audio_data['timestamp'], '%d-%m-%Y %H:%M.%S')
                url_audio = audio_data['url_audio']
                audio_name = url_audio.split('/')[-1]

                g = urllib.request.urlopen(url_audio)

                #Creating CSV file in case we have a new user
                if not os.path.exists(username):
                    os.makedirs(username)

                    with open(username+'/audio_list.csv', 'w', newline='') as csvfile:
                        fieldnames = ["ID","Nombre archivo","Timestamp","Fecha de calculo","F0","F1","F2","F3","F4","Intensidad","HNR","Local Jitter","Local Absolute Jitter", "Rap Jitter", "ppq5 Jitter","ddp Jitter","Local Shimmer","Local db Shimmer","apq3 Shimmer","aqpq5 Shimmer","apq11 Shimmer","dda Shimmer"]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        csvfile.close()

                #Storing the audio
                with open(username+'/'+audio_name, 'wb') as f:
                    f.write(g.read())
                    f.close()

                try:
                    #Now we also pass timestamp
                    res = scripts.audio_analysis(username+'/'+audio_name, audio_name, timestamp)
                    
                    #Writing the data on CSV files (now we also pass the audio's ID)
                    scripts.write_csv(res, username, username+"/audio_list.csv",id_audio)
                    scripts.write_csv(res, username, "historical.csv",id_audio)
                except:
                    with open('log.txt', 'a') as f:
                        f.write('[{0}] Hubo un error al analizar el archivo {1} del usuario {2}\n'.format(datetime.today().strftime('%Y-%m-%d %H:%M'), audio_name, username))
                        f.close()

        return HttpResponseRedirect('/historical/')

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
            res = scripts.audio_analysis(audio_name, audio.name)

            #Creating CSV file in case we have a new user
            if new_user:
                with open(username+'/audio_list.csv', 'w', newline='') as csvfile:
                    fieldnames = ["Nombre archivo","Timestamp","Fecha de calculo", "F0","F1","F2","F3","F4","Intensidad","HNR","Local Jitter","Local Absolute Jitter", "Rap Jitter", "ppq5 Jitter","ddp Jitter","Local Shimmer","Local db Shimmer","apq3 Shimmer","aqpq5 Shimmer","apq11 Shimmer","dda Shimmer"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    new_user = False
                    csvfile.close()
            
            #Writing the data on CSV files
            scripts.write_csv(res, username, username+"/audio_list.csv")
            scripts.write_csv(res, username, "historical.csv")

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
        csvfile.close()
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
        csvfile.close()
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

    if path != 'log':
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
    else:
        #With this we trigger the file download
        with open("log.txt", 'rb') as log_file:
            response = HttpResponse(log_file, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename=log.txt'
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
            date_list.append(row[3])
            #To get the desired value, we have to add 4 to the index received (the first 2 rows are for username, filename, timestamp and upload date)
            arg_list.append(row[int(index)+5])
        csvfile.close()
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
            date_list.append(row[3])
            #To get the desired value, we have to add 4 to the index received (the first 2 rows are for username, filename, timestamp and upload date)
            arg_list.append(row[int(index)+5])
        csvfile.close()
        #The data in the CSV is stored as strings, so we change it to the correct type
        date_list[1:]=[datetime.strptime(x, '%Y-%m-%d %H:%M') for x in date_list[1:]]
        arg_list[1:]=[float(x) for x in arg_list[1:]]

        #The first element of each list is the label, and the rest are the values
        df = pd.DataFrame(data={user_list[0]:user_list[1:],date_list[0]:date_list[1:],arg_list[0]:arg_list[1:]})
        fig = px.line(df, x=date_list[0], y=arg_list[0], color=user_list[0], template='plotly_dark')
        div = plot(fig, auto_open=False, output_type='div')
    return render(request,"display_graph.html", {
        "title":"Análisis histórico de {0}".format(arg_list[0]),
        "graph":div})

def user_list_view(request):
    #Renders a list with all users
    with open('historical.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        #Here we'll store the data that we need for the graph (username, date and the value that we want to show)
        user_list = []
        for row in csvreader:
            user_list.append(row[0])
        csvfile.close()
    return render(request, "user_list.html",{
        "title":"Selección de usuario",
        "users":[*set(user_list[1:])]
    })

def user_info_view(request):
    #Renders the info of the requested user
    user = request.GET["user"]

    with open(user+'/audio_list.csv') as csvfile:
        csvreader = csv.reader(csvfile)
        csv_list = []
        for row in csvreader:
            csv_list += [row]
        csv_list[0][2] = "Fecha más reciente"
        tup = []
        for i in range(2,len(csv_list[0])-1):
            tup += [[csv_list[0][i], csv_list[-1][i]]]
        csvfile.close()

    return render(request, "user_info.html",{
        "title":"Selección de usuario",
        "user":user,
        "args":tup
    })