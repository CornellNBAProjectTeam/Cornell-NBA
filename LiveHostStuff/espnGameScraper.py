from bs4 import BeautifulSoup
import urllib2
import pytz
from datetime import datetime
import loadModelAndPredict
import socket
from selenium import webdriver
import pandas
import numpy as np
import urllib

"""Scrape the current games off of ESPN"""
def scrapeGames():
	Games = []
	
	#Load the HTML page
	page = urllib.urlopen('http://espn.go.com/nba/schedule').read()
	soup = BeautifulSoup(page)
	
	#Grab the Schedule Object from the HTML
	getSchedule = soup.find(id="sched-container")
	
	#Get a list of a list of games per day
	gamesPerDay = getSchedule.findAll("div", { "class" : "responsive-table-wrap" })
	
	for game in gamesPerDay:
		tableObj = game.find("table", { "class" : "schedule has-team-logos align-left" })
		
		#Check if game is not a past one
		header = game.find("thead").find("tr").findAll("th")[2].find("span").text

		if header.strip() == "RESULT":
			#This is a past game
			continue
		elif header.strip() == "TIME":
			dateCaption = tableObj.find("caption").text
			gamesBody = tableObj.find("tbody").findAll("tr")
			
			for game in gamesBody:
				td_objects = game.findAll("td")
				away_td = td_objects[0].find("abbr").text
				home_td = td_objects[1].find("abbr").text
				if td_objects[2].text == "LIVE":
					time_td = "LIVE"
				else:
					time_td = UTC_to_EST(td_objects[2]["data-date"])
				
				#Note the Time_Td is given in UTC time
				#print away_td + "  " + home_td + "  " + time_td 
				
				#Append to our Games List
				Games.append((home_td,away_td,time_td ))
		else:
			raise Exception("NEW ERROR!")
				
	return Games
	

"""Convert the Game Date from UTC to Eastern Time"""
def UTC_to_EST(somestring):
	utc = pytz.utc
	eastern = pytz.timezone('US/Eastern')

	# Using datetime1 from the question
	datetime1 = datetime.strptime(somestring, "%Y-%m-%dT%H:%MZ")

	# Tell Python this is UTC Time
	utc_time = utc.localize(datetime1)

	# Convert from UTC time to Eastern Time
	eastern_time = utc_time.astimezone(eastern)

	return str(eastern_time)[0:str(eastern_time).rfind("-")]
	
def predictGames():
	games = scrapeGames()
	for (home,away,time) in games:
		scoreDifferential = loadModelAndPredict.makePrediction(home,away)
		if scoreDifferential > 0:
			print home + " will beat " + away + " by " + str(int(scoreDifferential)) + " points on " + time
		else:
			print away + " will beat " + home + " by " + str(-1*int(scoreDifferential)) + " points on " + time
		
	
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
	

def updateCurrentTeamRollingCSV():
	driver = webdriver.PhantomJS(executable_path='C:\\Users\\jd728\\Documents\\phantomjs-2.0.0-windows\\phantomjs-2.0.0-windows\\bin\\phantomjs.exe')
	ListOfTeams = grab_team_initials("2016")
	main_csv = "C:\\Users\\jd728\\Documents\\LiveHostStuff\\currentTeamRolling2.CSV" 
	with open(main_csv,'w+') as f1:
		f1.write("teamInitial,win,MP,FG,FGA,FG%,3P,3PA,3P%,FT,FTA,FT%,ORB,DRB,TRB,AST,STL,BLK,TOV,PF,TS%,eFG%,3PAr,FTr,ORB%,DRB%,TRB%,AST%,STL%,BLK%,TOV%,USG%,ORtg,DRtg" + '\n')
		
		for team in ListOfTeams:
			game_urls, opponentIDS, outcome = grab_game_urls(team,"2016",driver)
			columns = ["teamInitial", "win" , "MP" , "FG" , "FGA" , "FG%" , "3P" , "3PA" , "3P%" , "FT" , "FTA" , "FT%" , "ORB" , "DRB" , "TRB" , "AST" , "STL" , "BLK" , "TOV" , "PF" , "TS%" , "eFG%" , "3PAr" , "FTr" , "ORB%" , "DRB%" , "TRB%" , "AST%" , "STL%" , "BLK%" , "TOV%" , "USG%" , "ORtg" , "DRtg"]
			index = [i for i in range(0,len(game_urls))]
			finalDF = pandas.DataFrame(index=index,columns=columns)
			for urlI in range(0,len(game_urls)):
				basic_stats = ""
				basic_statsOP = ""
				teamWin = None
				
				while basic_stats == "" or basic_statsOP == "":
					basic_stats,advanced_stats, basic_statsOP, advanced_statsOP = aggregate_data(game_urls[urlI],team,str(opponentIDS[urlI]),driver)

					basicDF = basic_stats.split(",")
					basicDFOPP =basic_statsOP.split(",")
					advancedDF = advanced_stats.split(",")
					
					#We scored more points than the other team
					teamWin = float((int(basicDF[18]) > int(basicDFOPP[18])))
					
				#Add game stats to Data Frame
				finalDF.loc[urlI] = [team] + [teamWin] + [float(basicDF[i]) for i in range(0,18)] + [float(advancedDF[i]) for i in range(1,15)]
				
			finalDF = finalDF[columns[1:]].mean()
			
			newRollingAvg = list(finalDF)
			newRollingAvg = [str(x) for x in newRollingAvg]
			newRollingAvg = team + "," + ",".join(newRollingAvg)
			print newRollingAvg
			#Append the new rolling average
			f1.write(newRollingAvg + '\n')
				
	driver.close()
	
predictGames()