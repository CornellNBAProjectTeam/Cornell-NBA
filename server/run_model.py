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

from readMongo import readMongo, WANTED_FEATURES, PER_FEATURES

def flatten(objToFlatten):
	return [item for sublist in objToFlatten for item in sublist]

def BuildDataSet():
	# 1
	nbaFrame = readMongo(db='nba_stats', collection='games',
			query= {"date": {"$gte": datetime.datetime(2012, 1, 24, 7, 51, 5),"$lt": datetime.datetime(2012, 1, 25, 7, 51, 5)}}, queryReturn=WANTED_FEATURES, no_id=False,
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
	print specialDataSet
	return specialDataSet

#Calculates the Rolling Average of a team's stats up to a specific date. Input needs to be sorted by time first
def teamRollingAvg(seasonCSV, teamId):
	teamSet = seasonCSV[seasonCSV['tmA_abbreviation'] == teamId or seasonCSV['tmB_abbreviation'] == teamId]
	teamUpdatedSet = teamSet[teamSet.columns[1:]]
	teamUpdatedSet = teamUpdatedSet.shift(1) #No rolling average exists for the first game to use for predictions.
	teamUpdatedSet = pd.rolling_mean(teamUpdatedSet,window=teamSet.shape[0],min_periods=1)
	teamUpdatedSet = pd.concat([teamSet[teamSet.columns[0]],teamUpdatedSet],axis=1)
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
def GenerateRollingAverages(sorted_data,teams):
	teams = []
	team_rolls = []
	for i in range(0,len(teams)):
		team, team_rolling = teamRollingAvg(sorted_data,teams[i])
		teams.append(team)
		team_rolls.append(team_rolling)
	return teams, team_rolls

def PlotLearningCurve(X_data, y_data,algorithm, s_time):

	print('PlotLearningCurve called')

	# 1
	sizes = np.array([.1,.2,.5,.8,.99])

	train_sizes, train_scores, test_scores = learning_curve(
													algorithm,
													X_data,
													y_data,
													train_sizes=sizes)
	print('after learning_curve')
	train_mean = np.mean(train_scores, axis=1)
	train_std = np.std(train_scores, axis=1)
	test_mean = np.mean(test_scores, axis=1)
	test_std = np.std(test_scores, axis=1)

	# 2
	plt.figure(figsize=(15,10)) # Width, Height

	# Training Set
	plt.fill_between(train_sizes, train_mean-train_std,
					train_mean+train_std, alpha=0.1, color="r")

	# Cross Validation Set
	plt.fill_between(train_sizes, test_mean-test_std,
					test_mean+test_std, alpha=0.1, color="g")

	# Graph Legend text
	trainLabel = ('%.3f%% Training score' % (train_mean[4]))
	testLabel = ('%.3f%% Cross-validation score' % (test_mean[4]))

	# Plot lines
	plt.plot(train_sizes, train_mean, 'o-', color="r", label=trainLabel)
	plt.plot(train_sizes, test_mean, 'o-', color="g", label=testLabel)

	# Place title, X-axis label, Y-axis label
	plt.suptitle('Linear Regression: NBA PER', fontsize=20)
	plt.xlabel('Training examples')
	plt.ylabel('Accuracy')

	# Set limit on Y-axis, Place graph legend
	plt.ylim((0.5, 1.1))
	plt.xlim((0, 6500))
	plt.legend(loc="best")

	# Print duration of program
	print("--- %s seconds ---" % (time.time() - s_time))
	plt.show()

def Analysis(_deg=1):
	start_time = time.time()
	SortedDataSet = SortData(BuildDataSet())
	TeamIDS = GrabUniqueTeams(SortedDataSet)
	
	linear_regression = LinearRegression()

	# 2
	polynomial_features = PolynomialFeatures(degree=_deg, include_bias=False)

	# 3
	algorithm = Pipeline([("polynomial_features", polynomial_features),
						 ("linear_regression", linear_regression)])
	#========================================================================== */
	print('after Pipeline')

	# 4
	PlotLearningCurve(X, y, algorithm, start_time)

Analysis(3)