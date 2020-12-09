
#import pandas as pd
import requests
import flexpolyline as fp
from vincenty import vincenty as vc
from math import floor
import numpy as np
import pandas as pd

api_key="uMo8ZVdrrdwrdMUAttOx6W0ms4cTCp0oS-EypFl3gNQ"

def read_file(filename, nrows=None):
    data = pd.read_csv(filename, sep="\t", names=["user", "timestamp", "long", "lat"], nrows=nrows)
    data["timestamp"] = pd.to_datetime(data["timestamp"], yearfirst=True)
    return(data)

MAX_DIST = 0.1


def filter_rows(row, minLat, minLong, maxLat, maxLong) :
    return ( (minLat<row['lat']) & (maxLat>row['lat']) & (minLong<row['long']) & (maxLong>row['long']))
    

def getPath(departure, arrival): ## pts are (lat , lon)
#get a route from here API
    route = requests.get("https://router.hereapi.com/v8/routes?transportMode=pedestrian&origin="+str(departure[0])+","+str(departure[1])+"&destination="+str(arrival[0])+","+str(arrival[1])+"&return=polyline&apiKey="+api_key)
    print(route)
    path = fp.decode((route.json()["routes"][0]["sections"][0]["polyline"]))
    # re-sample the polyline 
    
    offset = 0
    pathRange = range (0,  len(path)-1)
    for i in pathRange :
        ptA = path[i+offset]
        ptB = path[i+1+offset]
        dist = vc(ptA, ptB)
        
        if dist>MAX_DIST:
            #how many pts should we add ?
            nbpts = floor(dist/MAX_DIST)

            #add intermediate pts
            for j in range(1, nbpts+1):
                newPt = ( ptA[0]+j*(ptB[0]-ptA[0])/(nbpts+1) , ptA[1]+j*(ptB[1]-ptA[1])/(nbpts+1))
                path.insert(i+j+offset, newPt)
            
            offset+=nbpts

            
    
    #compare the route with the heatmap to determine if we should exclude some areas
    # how to decide if we should exclude more areas ?
    # it pass through a case with a very low score 

    #get a new route with excluded areas
    return path
if __name__ == "__main__":
    #df1 = read_file('./privamov/privamov-gps', nrows=1000)# add your original dataset here
    
    
    ptA = ( 43.409484, 3.687372) ## lat and long of pt A
    ptB = ( 43.409461, 3.687383) ## lat and long of pt B

    '''
    minLat = min(ptA[0], ptB[0])
    minLong = min(ptA[1], ptB[1])
    maxLat = max(ptA[0], ptB[0])
    maxLong  = max(ptA[1], ptB[1])
    iter_csv = pd.read_csv('./privamov/privamov-gps', sep="\t", names=["user", "timestamp", "long", "lat"], nrows=1000, iterator=True, chunksize=10)
    df = pd.concat([chunk[filter_rows(chunk, minLat, minLong, maxLat, maxLong)] for chunk in iter_csv])
    '''
    print(getPath(ptA, ptB))
   
    
