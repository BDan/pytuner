'''
Created on 3 Dec 2014

@author: dbdan
'''
import argparse
import urllib
import os
import json
import sys
import hashlib
from bs4 import BeautifulSoup 
from collections import namedtuple
__version__ = "0.1.2"

Station = namedtuple("Station","url, name, description")
Stream = namedtuple("Stream", "url, bandwidth, type")
class StationQuery():
    debug=False
    debug=True
    
    search_url="http://tunein.com/search/?%s"
    cache_template="./cache/c_%s.tmp"
    def __init__(self,name):
        self.name=name
    
    def input_option(self,prompt,max_val):
        if max_val==1: return 0
        ret_val=0
        while True:
            try:
                ret_val=int(raw_input(prompt))
            except:
                print "Invalid"
                continue
            if ret_val>=0 and ret_val <max_val:
                return ret_val
            else:
                print "Out of range"
    
    def get_stream_desc(self,url):
        station_page= self.cached_download(url,self.debug)
        payload_str = station_page.split("TuneIn.payload =")[1].split("//TODO:")[0].strip()
        station=json.loads(payload_str)["Station"]["broadcast"]
        ret_val=[] 
        if len(station["Streams"])>0:
            for s in station["Streams"]:
                #print json.dumps(s, indent=4)
                ret_val.append(Stream(s["Url"],s["Bandwidth"],"WEB"))
        elif station["StreamUrl"].strip()=="":
            return []
        else:
            streams = json.loads(self.cached_download(station["StreamUrl"], self.debug)[1:-2])["Streams"]
            for s in streams:
                ret_val.append( Stream(s["Url"], s["Bandwidth"],s["MediaType"]))
        return ret_val
        
    def get_url(self):
        stations=self.search_term(self.name)
        if len(stations)==0:
            return "Nothing found"
        for i,s in enumerate(stations):
            print ("%d: %s (%s)"%(i,s.name, s.description)).encode("latin-1","replace")
        select = self.input_option("Station: ", len(stations))
        stream_desc = self.get_stream_desc("http://tunein.com"+stations[select].url)
        for i,s in enumerate(stream_desc):
            d_type=s.type
            if d_type=="WEB": d_type="Web only"
            print "%d: %s %dKb/s"%(i,d_type, s.bandwidth)
        if len(stream_desc)==0:
            return "No streams active"
        select = self.input_option("Stream: ", len(stream_desc))
        return stream_desc[select].url
    
    def cached_download(self,url,cache=False):
        if cache:
            cache_file=self.cache_template%hashlib.md5(url).hexdigest()
            if not os.path.exists(os.path.dirname(cache_file)):
                os.makedirs(os.path.dirname(cache_file))
            if os.path.isfile(cache_file):
                with open(cache_file,"r") as cache:
                    #print "DEBUG: reading cache file"
                    return cache.read()
        try:
            ret_val = urllib.urlopen(url).read()
        except IOError as e:
            print "Error accessing stream url: "+url
            print e
            return ""
            #
        if cache:
            with open(cache_file,"w") as cache:
                cache.write(ret_val)
        return ret_val
    
    def search_term(self, term):
        ret_val=[]
        print "Searching for: %s."%(term)
        url= self.search_url%urllib.urlencode({"query": term})
        search_page=self.cached_download(url,self.debug)
        soup = BeautifulSoup(search_page)
        section = soup.find("section", id="stationResults")
        if section==None:
            return []
        stations = section.find_all("a")
        for s in stations:
            
            url =  s["href"]
            show = s.find("span", class_="show")
            try: 
                title = show.find("h3").string
                description = show.find("p").string
                ret_val.append(Station(url, title, description))
            except AttributeError: pass
        return ret_val
        

def parse_arguments():
    parser = argparse.ArgumentParser(usage="%(prog)s [OPTIONS] station_name")
    version = ("%(prog)s {}. Copyright (C) 2014 Dan Bendas"
               ).format(__version__)
    parser.add_argument('-v', action="version",
                        version=version)
    
    parser.add_argument(nargs=argparse.REMAINDER, dest="station_name",
                        help="Station name")
    args = parser.parse_args()
    args._station_name = ' '.join(args.station_name)
    if not (args.station_name):
        parser.error("Missing station name.")

    return args



    args = parser.parse_args()
if __name__ == '__main__':
    #sys.argv+="Balkan".split()
    args = parse_arguments()
    query = StationQuery(args._station_name)
    print query.get_url()
