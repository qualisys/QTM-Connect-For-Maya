import requests
import numpy as np
import pandas as pd
import time as t

def GetData(Markers=True,hostIp = "127.0.0.1", Start = 0, End=0):
    reqString = "http://"+ hostIp + ":7979/api/experimental/measurements/"
    query = {}
    if Markers:
        query['Markers'] = 'true'
    if Start:
        query['Start'] = str(Start)
    if End:
        query['End'] = str(End)    
    #query = {'Markers':'true', 'Start':'0', "End":"10"}
    #query = {'Markers':'true'}
    #print(query)
    response = requests.get(reqString)
    messurmentsResponse = response.json()
    messurmentGUID = ""
    if len(messurmentsResponse):
        messurmentGUID = messurmentsResponse[0]
    else:
        print("No measurment open")
        return False
    #print(messurmentGUID)
    reqString += messurmentGUID + "/data"
    response = requests.get(reqString, params = query)
    #print("Request took: " + str(response.elapsed.total_seconds()))
    #print(response.content)
    #print(reqString)
    return response.json(),response.elapsed.total_seconds()
    #response = requests.get("http://localhost:7979/api/experimental/measurements/%7BF3480361-7FB7-11EC-AD03-00E04C0802BB%7D/data", params=query)
    #print(response.content)
    #rJson = response.json()
    #markers = rJson["Markers"]

def GetLabledMarkers(hostIp = "127.0.0.1",Range = [0,0], GetCurrentFrame = False):
    fileInfo,time = GetData(Markers=False)
    start = fileInfo["Timebase"]["Range"]["Start"]
    end = fileInfo["Timebase"]["Range"]["End"]
    if  Range[0]:
        if (start << Range[0]) &  (Range[0]<< end):
            start = Range[0]
        else:
            print("Start value: " + str(Range[0]) + " is outside of QTM set range: " + str(start) + " to " + str(end) + " setting start to: " + str(start))
    if  Range[1]:
        if (start << Range[1]) &  (Range[1]<< end):
            end = Range[1]    
        else:
            print("End value: " + str(Range[0]) + " is outside of QTM set range: "+  str(start) + " to " + str(end) + " setting end to: " + str(end))
    if GetCurrentFrame:
        start = fileInfo["CurrentFrame"]
        #end = fileInfo["CurrentFrame"]
        end = start + 9

    print(start)
    print(end)
    data,reqTime = GetData(Markers=True, hostIp = hostIp, Start = start, End = start+10)
    timeForTenFrames = reqTime
    framesToFetch = int(np.trunc(20/timeForTenFrames))
    estimatedTime = np.round((end-start+1)/10*timeForTenFrames)
    print("Fetching " + str(end-start+1) + " frames, estimated time: " + str(estimatedTime) + " seconds")
    #Create data structue
    
    markers = data["Markers"]
    marker_data ={}
    for marker in markers:    
        df = pd.DataFrame(index=range(start,end+1),columns=['x','y','z','residual'], dtype='float')
        df.name = marker["Name"]
        marker_data[marker["Name"]] = df
    
    for frameStart in range(start, end, framesToFetch):
        tic = t.perf_counter()
        print("Frame: "+ str(frameStart) + " to " + str(frameStart + framesToFetch-1))
        data,reqTime = GetData(Markers=True, Start = frameStart, End = frameStart+framesToFetch-1)
        remTime = int(np.round((end-frameStart) * reqTime/(framesToFetch-1)))
        print("Fetched: " + str(framesToFetch-1) + " frames in " + str(reqTime) + " second, approximate time left " + t.strftime('%H:%M:%S', t.gmtime(remTime)))
        
        markers = data["Markers"]
        for marker in markers:    
            #df = pd.DataFrame(index=range(start,end+1),columns=['x','y','z','residual'], dtype='float')
            for part in marker["Parts"]:
                part_start = part["Range"]["Start"]
                part_end = part["Range"]["End"]
                part_values = np.matrix(part["Values"])
                marker_data[marker["Name"]].loc[part_start:part_end]= part_values       
        toc = t.perf_counter()
        print(f"Fetch and sort the data in {toc - tic:0.4f} seconds")
    return marker_data,fileInfo