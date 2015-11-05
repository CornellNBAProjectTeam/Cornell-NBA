import pandas as pd
import cPickle
"""Loads our pretrained model from our dump and allows us to test with it"""

def loadClassifier():
	# load the classifier
	with open('BeastClassifier.pkl', 'rb') as fid:
		return cPickle.load(fid)
	
def saveClassifier(inputClassifier):
	# save the classifier
	with open('my_dumped_classifier.pkl', 'wb') as fid:
		cPickle.dump(inputClassifier, fid)    

def makePrediction(team1,team2):
	team1Rolling = grabRolling(team1)
	team2Rolling = grabRolling(team2)
	columns = ['tm0_win', 'tm0_MP', 'tm0_FG', 'tm0_FGA', 'tm0_FG%', 'tm0_3P', 'tm0_3PA', 'tm0_3P%', 'tm0_FT', 'tm0_FTA', 'tm0_FT%', 'tm0_ORB',
       'tm0_DRB', 'tm0_TRB', 'tm0_AST', 'tm0_STL', 'tm0_BLK', 'tm0_TOV',
       'tm0_PF', 'tm0_TS%', 'tm0_eFG%', 'tm0_3PAr', 'tm0_FTr',
       'tm0_ORB%', 'tm0_DRB%', 'tm0_TRB%', 'tm0_AST%', 'tm0_STL%',
       'tm0_BLK%', 'tm0_TOV%', 'tm0_USG%', 'tm0_ORtg', 'tm0_DRtg',
       'tm1_win', 'tm1_MP', 'tm1_FG', 'tm1_FGA', 'tm1_FG%', 'tm1_3P',
       'tm1_3PA', 'tm1_3P%', 'tm1_FT', 'tm1_FTA', 'tm1_FT%', 'tm1_ORB',
       'tm1_DRB', 'tm1_TRB', 'tm1_AST', 'tm1_STL', 'tm1_BLK', 'tm1_TOV',
       'tm1_PF', 'tm1_TS%', 'tm1_eFG%', 'tm1_3PAr', 'tm1_FTr',
       'tm1_ORB%', 'tm1_DRB%', 'tm1_TRB%', 'tm1_AST%', 'tm1_STL%',
       'tm1_BLK%', 'tm1_TOV%', 'tm1_USG%', 'tm1_ORtg', 'tm1_DRtg']
	   
	X = pd.DataFrame(index=[0],columns=columns)
	
	team1Rolling.columns = ["tm0_" + x for x in team1Rolling.columns]
	team2Rolling.columns = ["tm1_" + x for x in team2Rolling.columns]
	
	if not team1Rolling.empty:
		X.ix[0:1,0:33] = team1Rolling[team1Rolling.columns[1:]].values
	
	if not team2Rolling.empty:
		X.ix[0:1,33:] = team2Rolling[team2Rolling.columns[1:]].values

	#Fill Empty Values (In case a team hasn't played)
	X = X.fillna(0)
	
	classifier = loadClassifier()

	
	result = classifier.predict(X)
	
	return result
	
#We'll store the rolling averages for each team during the course of the season
#in a giant CSV. After each game, have the site auto update the team rolling information :D
def grabRolling(teamInitial):
	teamData = pd.read_csv("currentTeamRolling.csv")
	teamRow = teamData.loc[teamData['teamInitial'] == teamInitial]
	return teamRow