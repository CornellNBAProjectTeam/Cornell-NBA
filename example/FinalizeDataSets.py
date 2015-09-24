import os
import sys
sys.path.append('C:\\NBA Data Science\\')
import ScrapeWebsite

###Team Codes are just the indicies
def createTeamCodes(years = ["2008","2009","2010","2011","2012","2013","2014","2015"]):
	initials = []
	for year in years:
		initials.extend(ScrapeWebsite.grab_team_initials(year))
	allTeams = list(set(initials))
	return allTeams
	
teamCodes = createTeamCodes()

def createCSVPerSeason(years = ["2008","2009","2010","2011","2012","2013","2014","2015"]):
	inPath = "C:\\NBA Data Science\\Scrapped\\"
	newpath = "C:\\NBA Data Science\\Prepared\\"
	if not os.path.exists(newpath): os.makedirs(newpath)
	
	for year in years:
		initials = ScrapeWebsite.grab_team_initials(year) #We'll be using functions inside our ScrapeWebsite
		outputCSV = open(newpath + year + "_seasonDataSet.csv","w+")
		outputCSV.write("date,win,tm0_init,tm0_MP,tm0_FG,tm0_FGA,tm0_FG%,tm0_3P,tm0_3PA,tm0_3P%,tm0_FT,tm0_FTA,tm0_FT%,tm0_ORB,tm0_DRB,tm0_TRB,tm0_AST,tm0_STL,tm0_BLK,tm0_TOV,tm0_PF,tm0_PTS,tm0_TS%,tm0_eFG%,tm0_3PAr,tm0_FTr,tm0_ORB%,tm0_DRB%,tm0_TRB%,tm0_AST%,tm0_STL%,tm0_BLK%,tm0_TOV%,tm0_USG%,tm0_ORtg,tm0_DRtg,tm1_init,tm1_MP,tm1_FG,tm1_FGA,tm1_FG%,tm1_3P,tm1_3PA,tm1_3P%,tm1_FT,tm1_FTA,tm1_FT%,tm1_ORB,tm1_DRB,tm1_TRB,tm1_AST,tm1_STL,tm1_BLK,tm1_TOV,tm1_PF,tm1_PTS,tm1_TS%,tm1_eFG%,tm1_3PAr,tm1_FTr,tm1_ORB%,tm1_DRB%,tm1_TRB%,tm1_AST%,tm1_STL%,tm1_BLK%,tm1_TOV%,tm1_USG%,tm1_ORtg,tm1_DRtg" + "\n")
		
		for team in initials:
			basicCSV = open(inPath + year + "\\" + team + "_basic.csv", "r").read()
			advancedCSV = open(inPath + year + "\\" + team + "_advanced.csv","r").read()
			outcomeCSV = open(inPath + year + "\\" + team + "_outcome.csv","r").read()
			
			basicCSV = basicCSV.split('\n')
			advancedCSV = advancedCSV.split('\n')
			outcomeCSV = outcomeCSV.replace("G,Date,,,,,Opponent,,,Tm,Opp,W,L,Streak,Notes\n","") #Remove repeated headers from CSV
			outcomeCSV = outcomeCSV.split('\n')
			
			for i in range(0,len(basicCSV)):
				if basicCSV[i] != "" and advancedCSV[i] != "" and outcomeCSV[i] != "":
					#Create feature vectors
					outcomeFeatures = outcomeCSV[i].split(',')
					basicFeatures = basicCSV[i].split(',')
					advFeatures = advancedCSV[i].split(',')
					
					#Grab basic features for each team
					team0_basic = basicFeatures[0:19]
					team1_basic = basicFeatures[20:39]
					
					#Grab advanced features for each team (Ignore the duplicated MP feature that's already inside our basic dataset)
					team0_adv = advFeatures[1:15]
					team1_adv = advFeatures[16:]
					
					#Grab teamCode for opponent team by converting opponent's initial stored at the end of basicCSV
					print team + " " + year
					team1_initial = teamCodes.index(basicFeatures[40])
					
					#Grab teamCode for current team
					team0_initial = teamCodes.index(team)
					
					#Create team0 and team1 entry
					team0_entry = str(team0_initial) + "," + ','.join(team0_basic) + "," + ','.join(team0_adv)
					team1_entry = str(team1_initial) + "," + ','.join(team1_basic) + "," + ','.join(team1_adv)
					
					#Whether team0 won or lost
					team0_win = outcomeFeatures[7].replace("W","1").replace("L","0") #We'll get other values if our data is corrupted
					
					#Date of match between team0 and team1
					date_match = outcomeFeatures[1]
					
					#Add new data point to line in our seasonal data set
					outputCSV.write(date_match + "," + team0_win + "," + team0_entry + "," + team1_entry + "\n")
					
		#Close the file
		outputCSV.close()

if __name__ == "__main__":
	print "STARTING"
	createCSVPerSeason()
	print "FINISHED"