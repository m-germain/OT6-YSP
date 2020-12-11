
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
    

def getPath(departure, arrival, maxDist, avoid=None): 
    ## pts are (lat , lon)
    ## avoid : array of bbox coord (coord =  [minLat, minLon, maxLat, maxLon])
    ##avoid[areas]=bbox:minLong,minLat,maxLong,maxLat,bbox:.....
#get a route from here API
    url = "https://router.hereapi.com/v8/routes?transportMode=pedestrian&origin="+str(departure[0])+","+str(departure[1])+"&destination="+str(arrival[0])+","+str(arrival[1])+"&return=polyline&apiKey="+api_key
    if(avoid is not None and len(avoid)>0):
        avoidQuery = "&avoid[areas]="
        for i in range(0, len(avoid)):
            coords= avoid[i]
            avoidQuery= avoidQuery+ "bbox:"+str(coords[1])+","+str(coords[0])+","+str(coords[3])+","+str(coords[2])
            if(i<len(avoid)-1):
                avoidQuery+="|"
        url+=avoidQuery
    
    print(url)
    route = requests.get(url)
    print(route)
    #print(route.json()["routes"][0]["sections"][0]["polyline"])
    path = fp.decode((route.json()["routes"][0]["sections"][0]["polyline"]))
    # re-sample the polyline 
    
    offset = 0
    pathRange = range (0,  len(path)-1)
    for i in pathRange :
        ptA = path[i+offset]
        ptB = path[i+1+offset]
        dist = vc(ptA, ptB)
        
        if dist>maxDist:
            #how many pts should we add ?
            nbpts = floor(dist/maxDist)

            #add intermediate pts
            for j in range(1, nbpts+1):
                newPt = ( ptA[0]+j*(ptB[0]-ptA[0])/(nbpts+1) , ptA[1]+j*(ptB[1]-ptA[1])/(nbpts+1))
                path.insert(i+j+offset, newPt)
            
            offset+=nbpts

            
    
    #compare the route with the heatmap to determine if we should exclude some areas
    # how to decide if we should exclude more areas ?
    # it pass through a case with a very low score 
    ## strictly for testing :
    '''
    newPath=[]
    for elem in path:
        newPath.append((elem[1],elem[0]))
    print(newPath)
    invertedCoordPath = fp.encode(newPath, precision=8)
    print(invertedCoordPath)
    '''
    #get a new route with excluded areas
    return path
if __name__ == "__main__":
    #df1 = read_file('./privamov/privamov-gps', nrows=1000)# add your original dataset here
    
    '''
    ptA = ( 43.409484, 3.687372) ## lat and long of pt A
    ptB = ( 43.409461, 3.687383) ## lat and long of pt B

    
    minLat = min(ptA[0], ptB[0])
    minLong = min(ptA[1], ptB[1])
    maxLat = max(ptA[0], ptB[0])
    maxLong  = max(ptA[1], ptB[1])
    
    iter_csv = pd.read_csv('./privamov/privamov-gps', sep="\t", names=["user", "timestamp", "long", "lat"], nrows=1000, iterator=True, chunksize=10)
    df = pd.concat([chunk[filter_rows(chunk, minLat, minLong, maxLat, maxLong)] for chunk in iter_csv])
    print(df)
    '''
    ptA = (45.75690818337607, 4.830079854961481)
    ptB = (45.759896884178474, 4.852161131522244)
    print(getPath(ptA, ptB, 0.1))
    avoid =  [[4.84294, 45.75943, 4.84789, 45.76103],[4.84437, 45.75726, 4.84924, 45.75957]]
    print(getPath(ptA, ptB, 0.1, avoid))
   
    
