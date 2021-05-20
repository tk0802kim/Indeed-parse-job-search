# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 03:33:55 2021

@author: TaeKen
"""
import numpy as np

import pandas as pd
import pickle
import math
import copy
from tqdm import tqdm
import requests
import bs4
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
import re
import webbrowser
from datetime import datetime


location = ["New York, NY"]
site = 'indeed'

#load pickle
if 'indeed' in site:
    try:
        with open("indeed_listing.pkl","rb") as f:
            df_indeed = pickle.load(f)
    except:
        print('Making new joblists')

#%%
#additional fields
def scrap(location):
    from nordvpn_switcher import initialize_VPN,rotate_VPN
    
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'}
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko)Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36'}
    #headers = {'User-Agent':'Nokia5310XpressMusic_CMCC/2.0 (10.10) Profile/MIDP-2.1 Configuration/CLDC-1.1 UCWEB/2.0 (Java; U; MIDP-2.0; en-US; Nokia5310XpressMusic) U2/1.0.0 UCBrowser/9.5.0.449 U2/1.0.0 Mobile'}
    
    #vpn setup
    instructions = initialize_VPN(area_input=['united states'])
    rotate_VPN(instructions)
    
    #selenium
    driver = webdriver.Chrome()
    
    custom_fields=["applied","text","tags","date_collected",'Order','Outcome','date_applied']
    
    
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
                    df_indeed.set_index('jk',inplace=True)
                    
                for field in custom_fields:
                    if field not in df_indeed.columns:
                        df_indeed[field] = ''
                        
                        
                    # df_indeed["applied"]=''
                    # df_indeed["text"]=''
                    
                page_i += 50
                if page_i > 200:
                    break
                sleep(1)
    #%%
    """order maker and nan remover"""
    
    counter = int(df_indeed['Order'].max())+1
    for jk, row in df_indeed[::-1].iterrows():
        if np.isnan(row['Order']):
            df_indeed.loc[jk,'Order'] = counter
            counter+=1
        
        # for col in custom_fields:
        #     try:
        #         if np.isnan(row[col]):
        #             df_indeed.loc[jk,col] = ''
        #     except:
        #         continue
    
    df_indeed.fillna('',inplace=True)
    with open("indeed_listing.pkl","wb") as f:
        pickle.dump(df_indeed,f)
    #%%
    """description getter"""
    
    for jk, row in tqdm(df_indeed.iterrows()):
        url = "https://www.indeed.com/viewjob?jk="+jk
        
        if len(df_indeed['text'][jk])==0:
        
            html = requests.get(url,headers=headers)
            soup = BeautifulSoup(html.text, 'html.parser')
            
            while 'Captcha' in soup.title.text:
                #webbrowser.open('url', new=0)
                rotate_VPN(instructions)
                html = requests.get(url)
                soup = BeautifulSoup(html.text, 'html.parser')  
                
            result= soup.find('div', {'id':'jobDescriptionText'})
            df_indeed.loc[jk,'text']= result.text
        
        
        if len(df_indeed['date_collected'][jk])==0:
            df_indeed.loc[jk,'date_collected']=datetime.now().strftime("%m/%d/%Y")
        
    with open("indeed_listing.pkl","wb") as f:
        pickle.dump(df_indeed,f)
    
    
    
    """tagger"""
    for jk, row in df_indeed.iterrows():
        if len(df_indeed['text'][jk])!=0:
            #get phd stuff
            phd_list = ['phd','ph.d','ph d','ph. d']    
            for phd in phd_list:
                if re.search(phd, df_indeed.loc[jk,'text'], re.IGNORECASE):
                    # if type(df_indeed['tags'][jk])!=str:
                    #     df_indeed.loc[jk,'tags'] = 'phd'
                    # elif not('phd' in df_indeed.loc[jk,'tags']):
                    #     df_indeed.loc[jk,'tags'] = df_indeed.loc[jk,'tags']+', phd'
                    if len(df_indeed['tags'][jk])==0:
                        df_indeed.loc[jk,'tags'] = 'phd'
                    elif not('phd' in df_indeed.loc[jk,'tags']):
                        df_indeed.loc[jk,'tags'] = df_indeed.loc[jk,'tags']+', phd'
                        
    


#%%               
def parse_tags(*tags):
    #showlater
    if not tags:
        tags=['']

    for tag in tags:
        for i_ord in reversed(range(df_indeed.shape[0])):   
            
            jk = df_indeed.index[df_indeed['Order']==i_ord][0]
            url = "https://www.indeed.com/viewjob?jk="+jk    
            
            show_entry=False
            if (tag in df_indeed.loc[jk,'tags']) :
                if len(df_indeed.loc[jk,'applied'])==0:
                    show_entry = True
                elif (df_indeed.loc[jk,'applied']!='not') and not(df_indeed.loc[jk,'applied'][0].isnumeric()):
                    show_entry = True
                
                if show_entry:
                    webbrowser.open(url, new=0) 
                    donext = input("What's next? Type 'applied', 'not', 'later', or 'stop':   \n")
                   
                    if donext in ['applied','not','later']:
                        df_indeed.loc[jk,'applied']=donext
                        if donext == 'applied':
                            df_indeed.loc[jk,'applied'] = datetime.now().strftime("%m/%d/%Y")
                            
                    elif donext == 'stop':
                        break

        else:
            continue
                  
        with open("indeed_listing.pkl","wb") as f:
            pickle.dump(df_indeed,f)
            
        break

def update_status(company):
    hits = df_indeed.loc[(df_indeed['cmp']==company)&[len(entry)>6 for entry in df_indeed['applied']],:]
    for n, title in enumerate(hits['title']):
        print('{}: {}'.format(n+1,title))
    print(' ')
    i_job = input("Which one? \n")
    print(' ')
    result = input("Update Result \n")
    
    jk = hits.index[int(i_job)-1]
    df_indeed.loc[jk,'Outcome'] +='\n'+ result+' - '+datetime.now().strftime("%m/%d/%Y")
    
    with open("indeed_listing.pkl","wb") as f:
        pickle.dump(df_indeed,f)
        
        
        
        
        
        
        
        
        
# for i,row in df_indeed.iterrows():
#     if row.Order>=253:
#         df_indeed.loc[i,'Order'] = 302+(253-row.Order)