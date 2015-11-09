"""Model using the most basic features"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn import cross_validation
from sklearn import linear_model
from sklearn import svm
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.learning_curve import learning_curve
#Calculates the Rolling Average of a team's stats up to a specific date. Input needs to be sorted by time first
def teamRollingAvg(seasonCSV, teamId):
	teamSet = seasonCSV[seasonCSV['tm0_init'] == teamId]
	teamUpdatedSet = teamSet[teamSet.columns[1:]]
	teamUpdatedSet = teamUpdatedSet.shift(1) #No rolling average exists for the first game to use for predictions.
	teamUpdatedSet = pd.rolling_mean(teamUpdatedSet,window=teamSet.shape[0],min_periods=1)
	teamUpdatedSet = pd.concat([teamSet[teamSet.columns[0]],teamUpdatedSet],axis=1)
	return teamSet, teamUpdatedSet

#Loads and sorts the Seasonal Data Set by date
def loadAndSortData(year):
	folder = "Prepared/"
	data = pd.read_csv(folder + year + "_seasonDataSet.csv", header = False) #Loads our dataset

	#Convert date strings into type datetime
	data['date'] = pd.to_datetime(data['date'])
	
	#Sort our datarows by increasing date
	data = data.sort(['date'])
	
	return data

#Computes the rolling averages for all teams in the Sorted Data Set
def GenerateRollingAverages(sorted_data):
	teams = []
	team_rolls = []
	for i in range(0,34):
		team, team_rolling = teamRollingAvg(sorted_data,i)
		teams.append(team)
		team_rolls.append(team_rolling)
	return teams, team_rolls
	
"""Performs linear regression, indirectly predicting wins and losses by looking at the returned score differences"""
def trainScoreDifference(years = ['2008','2009','2010','2011','2012','2013','2014','2015']):
	year_errorSum = 0
	for year in years:
		#Loads the seasonal Data Set and sorts it by ascending date
		data = loadAndSortData(year)
	
		#Generate Team data and Rolling Averages data for each team in the data set
		teams, team_rolls = GenerateRollingAverages(data)
		
		featureDF = [] #The feature data frame (the features for our ML algorithm)
		targetDF = [] #The target data frame (the targets we're trying to predict, i.e. point differentials)
		
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
	
def scorerPTS(estimator, X, y):
	#Return's 1 (i.e. incorrect classification) when the ScoreDifference(y) has a different sign than the Predicted Score Difference
	#i.e. y=30 & predicted y = 10 -> outputs 0
	#i.e. y=10 & predicted y = (-)20 -> outputs 1 (incorrect classification due to different signs)
	actual = y.iloc[0][0]
	predicted = estimator.predict(X)[0][0]
	return int(actual*predicted <= 0)
	
def scorerPPTS(estimator, X, y):
	total = 0.0
	for i in range(0,X.shape[0]):
		total += scorerPTS(estimator,X.iloc[[i]],y.iloc[[i]])
	return (total/X.shape[0])

trainScoreDifference()#years = ['2014'])