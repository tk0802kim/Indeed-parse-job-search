# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 03:33:55 2021

@author: TaeKen
"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import math
import copy
from tqdm import tqdm
import requests
import bs4
from bs4 import BeautifulSoup
from time import sleep
from nordvpn_switcher import initialize_VPN,rotate_VPN
from selenium import webdriver
import re
import webbrowser
location = ["New York, NY"]
site = 'indeed'















#headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko)Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36'}
#headers = {'User-Agent':'Nokia5310XpressMusic_CMCC/2.0 (10.10) Profile/MIDP-2.1 Configuration/CLDC-1.1 UCWEB/2.0 (Java; U; MIDP-2.0; en-US; Nokia5310XpressMusic) U2/1.0.0 UCBrowser/9.5.0.449 U2/1.0.0 Mobile'}

#vpn setup
instructions = initialize_VPN(area_input=['united states'])
rotate_VPN(instructions)

#selenium
driver = webdriver.Chrome()

#load pickle
if 'indeed' in site:
    with open("indeed_listing.pkl","rb") as f:
        df_indeed = pickle.load(f)

#variables used
page_i = np.zeros(len(location),dtype=int)
stop = False

for i_loc, loc in enumerate(location):
    if 'indeed' in site:
        
        lstr = '+'.join(loc.split())
        
        while stop == False:           
            url = "https://www.indeed.com/jobs?q=data+scientist&l="+lstr+"&jt=fulltime&limit=50&sort=date&start="+str(page_i[i_loc])
            driver.get(url)
            jobmap = driver.execute_script('return jobmap')
            
            while 'Captcha' in driver.title:
                #webbrowser.open('url', new=0)
                rotate_VPN(instructions)
                driver.get(url)
                jobmap = driver.execute_script('return jobmap')
                
            # do stuff
            if "df_indeed" in locals():
                df_id = pd.DataFrame(jobmap.values())
                df_id.set_index('jk',inplace=True)
                
                df_list = [df_id.loc[row,:] for row in df_id.index if row not in df_indeed.index]
                
                df_indeed = df_indeed.append(df_list)                            
                
            else:
                df_indeed = pd.DataFrame(jobmap.values())
                df_indeed["applied"]=''
                df_indeed["text"]=''
                df_indeed.set_index('jk',inplace=True)
                
            page_i += 50
            if page_i > 300:
                break
            sleep(1)
            
            
for jk, row in tqdm(df_indeed.iterrows()):
    url = "https://www.indeed.com/viewjob?jk="+jk
    
    html = requests.get(url,headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    
    while 'Captcha' in soup.title.text:
        #webbrowser.open('url', new=0)
        rotate_VPN(instructions)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')  
        
    result= soup.find('div', {'id':'jobDescriptionText'})
    df_indeed.loc[jk,'text']= result.text
    
    #get phd stuff
    phd_list = ['phd','ph.d','ph d','ph. d']
    for phd in phd_list:
        if re.search(phd, result.text, re.IGNORECASE):
            df_indeed.loc[jk,'applied'] = 'phd'
    
with open("indeed_listing.pkl","wb") as f:
    pickle.dump(df_indeed,f)








def parse():
    for jk, row in df_indeed.iterrows():
        url = "https://www.indeed.com/viewjob?jk="+jk
        
        if (row['applied'] =='phd') and (row['applied']!='applied') and (row['applied']!='not'):
            
           webbrowser.open(url, new=0) 
           donext = input("What's next? Type 'applied', 'not', or 'stop'")
           
           if donext in ['applied','not']:
               df_indeed.loc[jk,'applied']=donext
           elif donext == 'stop':
               break
              
    with open("indeed_listing.pkl","wb") as f:
        pickle.dump(df_indeed,f)
