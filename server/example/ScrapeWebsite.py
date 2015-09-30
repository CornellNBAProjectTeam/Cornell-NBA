import urllib2
from bs4 import BeautifulSoup, SoupStrainer
from sys import argv
import pandas as pd
import string 
import os
from selenium import webdriver
import socket
import sys, getopt

"""A web scrapper that grabs Regular Season Game Data for every team in the NBA.
Data is obtained from www.basketball-reference.com """

"""Grab initials of all active franchises"""
def grab_team_initials(year):
	URL = 'http://www.basketball-reference.com/leagues/NBA_' + year + '.html'
	try:
		html = urllib2.urlopen(URL).read()
	except urllib2.URLError:
		print "Connect problem! Retrying soon..."
		return grab_team_initials(year)
	except:
		print "Unknown Error"
		return grab_team_initials(year)
		
		
	soup = BeautifulSoup(html)

	teams = soup.find('table',id="team")
	links = teams.findAll('a')
	listOfteams = []
	
	for link in links:
		if link['href'].startswith("/teams/"):# and link.parent.parent['class'][0] == "full_table":
			#This is an active team
			initial = link['href'].split('/')[2] #Remove the last char '/' from url
			listOfteams.append(initial) 
			#print initial
	return listOfteams

"""Gets a list of regular season games per team."""
def grab_game_urls(teamInitial,year,driver):
	for team in teamInitial:
		URL = 'http://www.basketball-reference.com/teams/' + 'TEAM_INITIAL' + '/' + 'YEAR' + '_games.html'
		driver.get(URL.replace("TEAM_INITIAL",teamInitial).replace("YEAR",year))
		html_source = driver.page_source
		soup = BeautifulSoup(html_source)
		
		links = soup.findAll('a',text='Box Score')
		opponentIDs = []
		listOfGames = []
	
	for link in links:
		if link.parent.parent.parent.parent["id"] == "teams_games_playoffs":
			#This is a PlayOff Season Game
			#print "PLAYOFF GAME"
			pass
		else:
			lrs = link.parent.parent.find_all('a')
			opID = ""
			for i in lrs:
				if i['href'].startswith("/teams/"):
					opID = i['href'].split("/")[2]
			opponentIDs.append(opID)
			listOfGames.append('http://www.basketball-reference.com' + link['href'])
			
		#Reads in the stats from the html table
	i = 0
	while i == 0:
		try:
			driver.execute_script("table2csv('teams_games')");
			i = 1
		except:
			print "FAILED... Retrying"
	
	html_source = driver.page_source
	soup = BeautifulSoup(html_source)
	
	WinLoss = soup.findAll('pre',id='csv_teams_games')[0].text
	return listOfGames,opponentIDs,'\n'.join(WinLoss.split('\n')[1:])

"""Grabs the seasonal team stat summary for all NBA teams"""
def aggregate_teamSeasonalData(year,driver):
	URL = "http://www.basketball-reference.com/leagues/NBA_" + year + ".html"
	
	#Prevents program from abruptly ending
	try:
		driver.get(URL)
	except socket.timeout:
		print "Failed to grab URL"
		return aggregate_teamSeasonalData(year,driver)
	except:
		print "Unknown Error"
		return aggregate_teamSeasonalData(year,driver)
		
	
	try:
		driver.execute_script("table2csv('team')")
		driver.execute_script("table2csv('opponent')")
		driver.execute_script("table2csv('shooting')")
		driver.execute_script("table2csv('shooting_opp')")
	except:
		print "Failed to call JavaScript"
		return aggregate_teamSeasonalData(year,driver)
	

	team = driver.find_element_by_id('csv_team').text
	opponent = driver.find_element_by_id('csv_opponent').text
	shooting = driver.find_element_by_id('csv_shooting').text
	opp_shooting = driver.find_element_by_id('csv_shooting_opp').text
	
	team = '\n'.join(team.split('\n')[1:-1])
	opponent = '\n'.join(opponent.split('\n')[1:-1])
	shooting = '\n'.join(shooting.split('\n')[3:-1])
	opp_shooting = '\n'.join(opp_shooting.split('\n')[3:-1])
	
	return team + '\n\n' + opponent + '\n\n' + shooting + '\n\n' + opp_shooting
	
"""Grabs the specific team NBA data sets"""
def aggregate_data(url,home_initial,opp_initial,driver):
	#Sets the Seconds TimeOut in case driver.get(url) hangs indefinitely
	socket.setdefaulttimeout(30)
	
	#Prevents program from abruptly ending
	try:
		driver.get(url)
	except socket.timeout:
		print "Failed to grab URL"
		return aggregate_data(url,home_initial,opp_initial,driver)
	except socket.error:
		print "Failed to grab URL"
		return aggregate_data(url,home_initial,opp_initial,driver)
	except:
		print "Unknown Error"
		return aggregate_data(url,home_initial,opp_initial,driver)
		
		
	
	try:
		driver.execute_script("table2csv('" + home_initial + "_basic')")
		driver.execute_script("table2csv('" + home_initial + "_advanced')")
		
		driver.execute_script("table2csv('" + opp_initial + "_basic')")
		driver.execute_script("table2csv('" + opp_initial + "_advanced')")
	except:
		print "Failed to call JavaScript"
		return aggregate_data(url,home_initial,opp_initial,driver)
	
	home_stats_basic = driver.find_element_by_id('csv_' + home_initial + '_basic').text
	home_stats_advanced = driver.find_element_by_id('csv_' + home_initial + '_advanced').text
	
	opp_stats_basic = driver.find_element_by_id('csv_' + opp_initial + '_basic').text
	opp_stats_advanced = driver.find_element_by_id('csv_' + opp_initial + '_advanced').text
	
	##Starters,MP,FG,FGA,FG%,3P,3PA,3P%,FT,FTA,FT%,ORB,DRB,TRB,AST,STL,BLK,TOV,PF,PTS
	home_stats_basic = ','.join(home_stats_basic.split('\n')[-1].split(',')[1:]) #Grabs Home BASIC Data
	opp_stats_basic = ','.join(opp_stats_basic.split('\n')[-1].split(',')[1:]) #Grabs Opp BASIC Data
	
	##Starters,MP,TS%,eFG%,3PAr,FTr,ORB%,DRB%,TRB%,AST%,STL%,BLK%,TOV%,USG%,ORtg,DRtg
	home_stats_advanced = ','.join(home_stats_advanced.split('\n')[-1].split(',')[1:]) #Grabs Home ADV Data
	opp_stats_advanced = ','.join(opp_stats_advanced.split('\n')[-1].split(',')[1:]) #Grabs Opp ADV Data
	
	return home_stats_basic, home_stats_advanced, opp_stats_basic, opp_stats_advanced

"""Main Function"""
def grabData(years = ["2013","2014"]):
	i = 0.0
	driver = webdriver.PhantomJS(executable_path='C:\\phantomjs-2.0.0-windows\\bin\\phantomjs.exe')
	for year in years:
		"""Stores the seasonal team data summary set"""
		newpath = "C:\\NBA Data Science\\Scrapped\\" + year
		if not os.path.exists(newpath): os.makedirs(newpath)
		seasonalTeamData = open("C:\\NBA Data Science\\Scrapped\\" + year + "\\team_data.csv",'w+')
		team_data = aggregate_teamSeasonalData(year,driver)
		seasonalTeamData.write(team_data)
		seasonalTeamData.close()
		
		initials = grab_team_initials(year)
		for team in initials:
			folder = "C:\\NBA Data Science\\Scrapped\\" + year + "\\" + team
			with open(folder + "_" + "basic.csv",'w+') as f1:
				with open(folder + "_" + "advanced.csv",'w+') as f2:
					with open(folder + "_" + "outcome.csv",'w+') as f3:
							game_urls, opponentIDS, outcome = grab_game_urls(team,year,driver)
							for urlI in range(0,len(game_urls)):
								basic_stats = ""
								basic_statsOP = ""
								
								#In case our error catching fails and we retrieve blank lines (can happen)
								while basic_stats == "" or basic_statsOP == "":
									basic_stats,advanced_stats, basic_statsOP, advanced_statsOP = aggregate_data(game_urls[urlI],team,str(opponentIDS[urlI]),driver)
								
								f1.write(basic_stats + "," + basic_statsOP + "," + str(opponentIDS[urlI]) + '\n')
								f2.write(advanced_stats + "," + advanced_statsOP + '\n')
								print game_urls[urlI]
							i = i + 1
							f3.write(outcome + '\n')
							print (str(i/(len(initials)*len(years)*1.0)) + "% complete")
	driver.close()
	
if __name__ == "__main__":
	print "START"
	grabData(years = ["2008","2009","2010","2011","2012","2013","2014","2015"])
	print "DONE"