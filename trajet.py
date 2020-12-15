
#import pandas as pd
import requests
import flexpolyline as fp
from vincenty import vincenty as vc
from math import floor
import numpy as np
import pandas as pd
from query_heatmap import QueryHeatMap

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
    route = requests.get(url)
    print(route)
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

    return path

def groupCells(cellA, cellB):
    #cell=(lat_min, long_min, lat_max, long_max) 
    if(cellA[0]==cellB[0] and cellA[2]==cellB[2]):
        if(cellA[1]==cellB[3]):
            return(cellA[0], cellB[1], cellA[2], cellA[3])
        elif(cellA[3]==cellB[1]):
            return(cellA[0], cellA[1], cellA[2], cellB[3])
    elif(cellA[1]==cellB[1] and cellA[3]==cellB[3]):
        if(cellA[0]==cellB[2]):
            return(cellB[0], cellA[1], cellA[2], cellA[3])
        elif(cellA[2]==cellB[0]):
            return(cellA[0], cellA[1], cellB[2], cellA[3])

    ##if two cells have an angle in common, we also group them
    elif( (cellA[1]==cellB[3] and cellA[0]==cellB[2]) or (cellA[3]==cellB[1] and cellA[0]==cellB[2]) 
    or (cellA[1]==cellB[3] and cellA[2]==cellB[0]) or (cellA[3]==cellB[1] and cellA[2]==cellB[0])):
        return(min(cellA[0], cellB[0]), min(cellA[1],cellB[1]), max(cellA[2],cellB[2]), max(cellA[3],cellB[3]))

    return None


def getToExclude(path, heatmap, threshold, toExclude, maxValue, minSize=None):
    if(minSize is None):
        minSize=0.01
    for cell in path:
        heatmap_value, lat_min, long_min, lat_max, long_max = heatmap.query_heatmap(cell[0],cell[1])
        if(heatmap_value/maxValue)<threshold:
            toExclude.append((lat_min, long_min, lat_max, long_max))
            
    #regroup areas in bigger areas
    offset = 0

    for n in range(0,5):
        for i in range(0, len(toExclude)-1):
            newCell = groupCells(toExclude[i-offset], toExclude[i-offset+1])
            if not (newCell is  None):
                toExclude[i-offset] = newCell
                toExclude.pop(i+1-offset)
                offset+= 1

    defExclude = []
    for cell in toExclude:
        size=vc((cell[0],cell[1]),(cell[2], cell[1]))*vc((cell[0],cell[1]),(cell[0],cell[3]))
        if(size>minSize):
            defExclude.append(cell)

    defExclude.sort(key=lambda cell : vc((cell[0],cell[1]),(cell[2], cell[1]))*vc((cell[0],cell[1]),(cell[0],cell[3])))
    return defExclude[0:20]

def getPathLength(path):

    length =0
    for i in range(0, len(path)-1):
        length+= vc(path[i], path[i+1])

    return length

def getPathScore(path, heatmap):
    score =0
    for cell in path:
        score += heatmap.query_heatmap(cell[0],cell[1])[0]
    return score

def getBestPath(departure, arrival, minExcludeArea, threshold): 

    heatmap = QueryHeatMap()
    maxDist= 0.1
    maxValue = heatmap.get_max_value()
    paths = []
    firstPath = getPath(departure, arrival, maxDist)
    prevExcludes = []
    excludes = getToExclude(firstPath, heatmap, threshold, [], maxValue, minExcludeArea)
    paths.append(firstPath)
    for i in range(1, 100):
        if(set(prevExcludes)==set(excludes)): ##ether we have a good path or we can not exclude anymore areas
            if(len(excludes)<20):
                print("perfect path")
            else:
                print("we excluded the 20 biggest areas after "+str(i)+" itterations")
            break
        else:
            paths.append(getPath(departure, arrival, maxDist, excludes))
            prevExcludes = excludes.copy()
            excludes = getToExclude(paths[i], heatmap, threshold, excludes, maxValue, minExcludeArea)

    firstPathLength = getPathLength(firstPath)

    paths.sort(key=lambda path : getPathScore(path, heatmap))
    print(str(len(paths))+ " itterations to find this path")
    for i in range(1, len(paths)+1):
        ##don't return a path which multiplies the distance by more than 1.5 
        if getPathLength(paths[len(paths) - i])<firstPathLength*1.5:
            return (heatmap.get_heatmap(), firstPath, paths[len(paths) - i])

    return (heatmap.get_heatmap(), firstPath, firstPath)


if __name__ == "__main__":
    #df1 = read_file('./privamov/privamov-gps', nrows=1000)# add your original dataset here

    ptA = (45.786839, 4.879130)
    ptB = (45.782746, 4.878132)
    ptC = (45.764346, 4.863172)
    path = getBestPath(ptA, ptC, None, 0.5)
    print(path[1])
    print(path[2])

    

   
