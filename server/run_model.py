import time
import pandas as pd
import numpy as np
import datetime

# Machine Learning algorithms
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures,scale
from sklearn.cross_validation import train_test_split, KFold
from sklearn.learning_curve import learning_curve


# Plot modules

import matplotlib.pyplot as plt
from matplotlib import style
style.use("ggplot")
pd.options.display.max_columns = 50
pd.set_option('expand_frame_repr', False)

# Custom modules

from read_mongo import readMongo, WANTED_FEATURES, PER_FEATURES

def flatten(objToFlatten):
	return [item for sublist in objToFlatten for item in sublist]

def BuildDataSet():
	# 1
	nbaFrame = readMongo(db='nba_stats', collection='games',
			query= {"date": {"$gte": datetime.datetime(2012, 4, 19, 7, 51, 5),"$lt": datetime.datetime(2012, 6, 21, 7, 51, 5)}}, queryReturn=WANTED_FEATURES, no_id=False,
			mongo_uri='mongodb://nba_stats_loginName:CUnba2015Log@ds033153.mongolab.com:33153/nba_stats')
	
	nbaFrame.ix[[0]].to_csv("Out.txt")

	statsDF = pd.DataFrame(list(flatten(nbaFrame.box)))
	teamDF = pd.DataFrame(list(flatten(nbaFrame.teams)))
	stats = pd.DataFrame(list(statsDF.team))
	date = nbaFrame.date

	newData = pd.concat([teamDF,stats],axis=1)

	Winners = newData[newData['won'] == 1]
	Losers = newData[newData['won'] == 0]

	Winners = Winners.rename(columns=lambda x: "tmA_" + x).reset_index(drop=True)
	Losers = Losers.rename(columns=lambda x: "tmB_" + x).reset_index(drop=True)

	specialDataSet = pd.concat([date,Winners,Losers],axis=1)
	#print specialDataSet[["tmA_name","tmB_name"]]
	return specialDataSet

#Calculates the Rolling Average of a team's stats up to a specific date. Input needs to be sorted by time first
def teamRollingAvg(seasonCSV, teamId):
	teamSet = seasonCSV[seasonCSV['tmA_abbreviation'] == teamId]
	teamUpdatedSet = teamSet[teamSet.columns[1:]]
	teamUpdatedSet = teamUpdatedSet.shift(1) #No rolling average exists for the first game to use for predictions.
	
	team_string_data = teamUpdatedSet[['tmA_abbreviation','tmA_name','tmB_abbreviation','tmB_name']] #Can't compute rolling average of a string
	team_numeric_data = teamUpdatedSet[['tmA_score','tmA_home','tmA_won','tmA_ast','tmA_blk','tmA_drb','tmA_fg','tmA_fg3','tmA_fg3_pct','tmA_fg3a','tmA_fg_pct','tmA_fga','tmA_ft', \
										'tmA_ft_pct','tmA_fta','tmA_mp','tmA_orb','tmA_pf','tmA_pts','tmA_stl','tmA_tov','tmA_trb','tmB_home','tmB_score','tmB_won','tmB_ast','tmB_blk' \
										,'tmB_drb','tmB_fg','tmB_fg3','tmB_fg3_pct','tmB_fg3a','tmB_fg_pct','tmB_fga','tmB_ft','tmB_ft_pct','tmB_fta','tmB_mp','tmB_orb','tmB_pf','tmB_pts','tmB_stl','tmB_tov','tmB_trb']]

	teamUpdatedSet = pd.rolling_mean(team_numeric_data,window=teamSet.shape[0],min_periods=1)
	teamUpdatedSet = pd.concat([teamSet['tmA_abbreviation'],teamUpdatedSet],axis=1)
	
	teamSet = teamSet[teamSet.columns[0:4]]
	teamUpdatedSet = teamUpdatedSet[teamUpdatedSet.columns[0:4]]
	return teamSet, teamUpdatedSet
	
def GrabUniqueTeams(data):
	teams = pd.concat([data['tmA_abbreviation'],data['tmB_abbreviation']],axis=0)
	teams = teams.drop_duplicates(take_last=True).reset_index(drop=True)
	return teams
	
#Sorts dataset by increase date
def SortData(data):
	#Convert date strings into type datetime
	data['date'] = pd.to_datetime(data['date'])
	
	#Sort our datarows by increasing date
	data = data.sort(['date'])
	
	return data

#Computes the rolling averages for all teams in the Sorted Data Set
def GenerateRollingAverages(sorted_data,teamIDS):
	teams = {}
	team_rolls = {}
	for team_abv in teamIDS:
		team, team_rolling = teamRollingAvg(sorted_data,team_abv)
		teams[team_abv] = team
		team_rolls[team_abv] = team_rolling
	return teams, team_rolls

def trainScoreDifference():
	year_errorSum = 0
	#Start time, used to figure out how long our algorithm takes
	start_time = time.time() 
	
	#Sort our Data Set by ascending date
	SortedDataSet = SortData(BuildDataSet())
	
	#Create a list of all the Team ID's within our SortedDataSet
	TeamIDS = GrabUniqueTeams(SortedDataSet) 

	#Create day to day rolling averages for each team in TeamIDS
	teams, team_rolls = GenerateRollingAverages(SortedDataSet,TeamIDS)
		
	featureDF = [] #The feature data frame (our independent variables)
	targetDF = [] #The target data frame (our dependent variable. win/loss)
	
	for tm in range(0,len(teams)):
		team = teams[tm] #The Original Data set for team tm
		team_rolling = team_rolls[tm] #The Rolling Data set for team tm.
		if not team.empty:
			"""Each Row N in team_rolling is the Predicted Rolling Average for game N using the previous N-1 games, thus Row 0 is NAN
			We'll use Row N (Predicted Feature based off of Rolling Average) to help predict the outcome of game N
			So the idea is that we'll use the rolling average of previous games to help predict the outcome of each upcoming game"""
			columns = ['PTS_DIFF','tm0_win','tm0_MP','tm0_FG','tm0_FGA','tm0_FG%','tm0_3P','tm0_3PA','tm0_3P%','tm0_FT','tm0_FTA','tm0_FT%','tm0_ORB','tm0_DRB','tm0_TRB','tm0_AST','tm0_STL','tm0_BLK','tm0_TOV','tm0_PF','tm0_TS%','tm0_eFG%','tm0_3PAr','tm0_FTr','tm0_ORB%','tm0_DRB%','tm0_TRB%','tm0_AST%','tm0_STL%','tm0_BLK%','tm0_TOV%','tm0_USG%','tm0_ORtg','tm0_DRtg','tm1_win','tm1_MP','tm1_FG','tm1_FGA','tm1_FG%','tm1_3P','tm1_3PA','tm1_3P%','tm1_FT','tm1_FTA','tm1_FT%','tm1_ORB','tm1_DRB','tm1_TRB','tm1_AST','tm1_STL','tm1_BLK','tm1_TOV','tm1_PF','tm1_TS%','tm1_eFG%','tm1_3PAr','tm1_FTr','tm1_ORB%','tm1_DRB%','tm1_TRB%','tm1_AST%','tm1_STL%','tm1_BLK%','tm1_TOV%','tm1_USG%','tm1_ORtg','tm1_DRtg']
			teamCOLS = ['win','tm0_MP','tm0_FG','tm0_FGA','tm0_FG%','tm0_3P','tm0_3PA','tm0_3P%','tm0_FT','tm0_FTA','tm0_FT%','tm0_ORB','tm0_DRB','tm0_TRB','tm0_AST','tm0_STL','tm0_BLK','tm0_TOV','tm0_PF','tm0_TS%','tm0_eFG%','tm0_3PAr','tm0_FTr','tm0_ORB%','tm0_DRB%','tm0_TRB%','tm0_AST%','tm0_STL%','tm0_BLK%','tm0_TOV%','tm0_USG%','tm0_ORtg','tm0_DRtg']
			dataD = np.array([np.arange(82)]*67,dtype="float").T
			dataD[:] = np.NAN
			predDF = pd.DataFrame(data = dataD,columns=columns)
			predDF = predDF.convert_objects(convert_numeric=True)
			vals = 0
			#Look at each match in our specified team's data set
			for match in range(1,team_rolling.shape[0]): #Note we start at index 1 to ignore the team's first match (rolling average of 1st match is NAN)
				#Grabs the timestamp and opponent id from the match
				time_stamp = team_rolling.iloc[match]['date']
				opponent_id = team.iloc[match]['tm1_init']
					
				#Grab the Opponent's most recent rolling average at a date BEFORE/EQUAL to our match's date (time_stamp)
				opponent_rolling = team_rolls[opponent_id][team_rolls[opponent_id]['date'] <= time_stamp][-1:]
				
				#If Opponent has no rolling_data to base off...(i.e. all entries NAN) Don't add the match to our predDF dataframe, i.e. pass
				if np.all(opponent_rolling.iloc[0][1:].isnull()):
					pass
				else:
					#Set the predicted (rolling) features for the opponent in the team_rolling DataFrame
					predDF.iloc[vals,0:1] = team.iloc[[match]]['win'].values #team.iloc[[match]]['tm0_PTS'].values - team.iloc[[match]]['tm1_PTS'].values
					predDF.ix[vals,columns[1:34]] = team_rolling.iloc[[match]][teamCOLS].values
					predDF.ix[vals,columns[34:]] = opponent_rolling.iloc[[0]][teamCOLS].values
					vals = vals + 1 #Increment our DataFrame index
					
			predDF = predDF.iloc[0:vals] #All rows after (vals-1) are NAN (i.e. empty)
			
			#Grab our selected target feature
			result = predDF.iloc[:,0:1]
			
			#Subtract the rolling averages to give some type of comparison
			new_features = predDF.ix[:,1:]
			
			"""Remove NAN row (can't make any useful predictions for 1st game)"""
			if not new_features.empty: #Not all teams may be in our season. i.e. Seattle SuperSonics isn't in year 2008 and on. They were renamed to Oklahoma City Thunder (OKC)
				new_features = new_features.drop(new_features.index[[0]])
				result = result.drop(result.index[[0]])
			
			#Add to our training data
			featureDF.append(new_features)
			targetDF.append(result)
		
		X = pd.concat(featureDF) #Combine all individual team predictions into 1 large data frame
		y = pd.concat(targetDF) #Combine all individual team targets into 1 large data frame
		
		#Create a prediction model using Linear Regression (Minimum Least Squares error)
		clf = svm.SVC(kernel='linear', C = 1.0)
		y = y.values.ravel()
			
		#Feature Normalization
		X = preprocessing.scale(X)
			
		X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.2)#, random_state=None)
		clf.fit(X_train, y_train)
		
		TrainScores = 1 - clf.score(X_train,y_train)
		TestScores = 1 - clf.score(X_test,y_test)
		
		year_errorSum += TestScores
		print('Year:' + year + ' Training Error: %.4f' % TrainScores)
		print('Year:' + year + ' Testing Error: %.4f' % TestScores)
	print('Average Testing Error: %.4f' % (year_errorSum/len(years)))

def Analysis():
	trainScoreDifference()


Analysis()