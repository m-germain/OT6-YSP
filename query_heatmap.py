import numpy as np 
from vincenty import vincenty as vc

class QueryHeatMap:
    """
    This class let us read an heatmapfile from a port lat long coordinates.


    Comment m'utiliser ? Et bien c'est tres simple jamy https://www.youtube.com/watch?v=eVxjTDvdaL0&ab_channel=Zeldemir

    1. importer la class :
    from query_heatmap import QueryHeatMap

    2. créer la heatmap ajd comme ca dimanche il y aura la date en plus :
    heatmap = QueryHeatMap()

    3. faire des query comme un petit fou : 
    heatmap_value, lat_min, long_min, lat_max, long_max = heatmap.query_heatmap(45.782029,4.877036)

    ce qui va renvoyer :
    heatmap_value, min_lat, min_long, max_lat, max_long
    (11891.0, 45.78229045023726, 4.878610329383891, 45.783191189573756, 4.879900549763038)
    """

    dist_cells = 0.1

    #Lyon Map Coordinates

    # MAX Point
    meximiax_lat = 45.904791
    meximiax_long = 5.186973

    # Min Point
    granger_lat = 45.524679
    granger_long = 4.642500


    dist_lat = vc((meximiax_lat,meximiax_long),(granger_lat,meximiax_long))
    dist_long = vc((meximiax_lat,meximiax_long),(meximiax_lat,granger_long))
    """
    +-----------+
    |           |
    |           |
    |           |
    |           |
    +-----------+
    """
    number_of_long_cells = round(dist_long / dist_cells)
    number_of_lat_cells  = round(dist_lat / dist_cells)


    long_cell_size = (meximiax_long - granger_long)/number_of_long_cells
    lat_cell_size = (meximiax_lat - granger_lat)/number_of_lat_cells

    Lon = np.arange(granger_long, meximiax_long, long_cell_size)
    Lat = np.arange(granger_lat, meximiax_lat, lat_cell_size) 


    # Fonction to switch between point lat:
    # Return : index_lat, index_long
    def lat_long_to_indexs(self, lat ,long):
        # Input Lat - Min lat
        lat_dist_from_min = vc((lat,self.granger_long),(self.granger_lat,self.granger_long))
        index_lat = lat_dist_from_min / self.dist_cells
        
        long_dist_from_min = vc((self.granger_lat,long),(self.granger_lat,self.granger_long))
        index_long = long_dist_from_min / self.dist_cells
        return index_lat,index_long

    # Fonction to extrapolate the box coordinate from a cell of the heatmap.
    # Return (lat_min,long_min,lat_max,long_max)
    """
                                   / ( lat_max,long_max )
                            +-----+
                            |     |
                            |  x  |
                            +-----+
    (lat_min,long_min ) /
    """

    def index_to_cbox(self, index_lat,index_long):
        long_index = round(index_long)
        lat_index = round(index_lat)
        return self.Lat[lat_index], self.Lon[long_index], self.Lat[lat_index+1], self.Lon[long_index+1]

    def __init__(self, date = 0):
        season, week, night = self.get_date_params(date)
        filename = get_filename(season, week, night)
        self.heatmap = np.load('data.npy')

    def get_date_params(self,date):
        night = False
        week = False
        season = 1
        if (date.hour) > 18: 
            night = True
        # week-end
        if (date.day > 5):
            week = True
        # Season    
        month = date.month
        if (month < 3): 
            season = 1
        elif (month < 6): 
            season = 2
        elif (month < 9):
            season =3 
        else: 
            season = 4 
        return season, week, night 

    def query_heatmap(self,lat, long): 
        index_lat, index_long = self.lat_long_to_indexs(lat,long)
        lat_min, long_min, lat_max, long_max = self.index_to_cbox(index_lat, index_long)
        return self.heatmap[round(index_lat)][round(index_long)], lat_min, long_min, lat_max, long_max

    def get_cell_size(self):
        return (self.lat_cell_size, self.long_cell_size)
    
    def get_max_value(self):
        #gruge pour normaliser les valeurs
        return np.max(self.heatmap)

    def get_heatmap(self):
        return self.heatmap


    def get_filename(self, season, week, night):
        if season == 1: 
            if week: 
                if night:
                    res="printemps/week/day"
                else:
                    res="printemps/week/night"
            else: 
                if night:
                    res="printemps/wend/day"
                else:
                    res="/wend/night"
        elif season == 2: 
            if week: 
                if night:
                    res="ete/week/day"
                else:
                    res="ete/week/night"
            else: 
                if night:
                    res="ete/wend/day"
                else:
                    res="ete/wend/night"
        elif season == 3:
            if week: 
                if night:
                    res="automne/week/day"
                else:
                    res="automne/week/night"
            else: 
                if night:
                    res="automne/wend/day"
                else:
                    res="automne/wend/night"
        elif season == 4: 
            if week: 
                if night:
                    res="hiver/week/day"
                else:
                    res="iver/week/night"
            else: 
                if night:
                    res="/wend/day"
                else:
                    res="hiver/wend/night"
        return f"{res}/data.npy"
