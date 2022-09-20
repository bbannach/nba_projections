import pandas as pd
import numpy as np
import random as rnd
import streamlit as st
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode


player_ratings = pd.read_csv('player_ratings.csv')
minutes_projections = pd.read_csv('DARKO_daily_projections_2022-08-28.csv')
player_ratings = player_ratings.merge(minutes_projections[['Player','Minutes']],how="left",on="Player")


#player_ratings['o_value'] = player_ratings['O-DPM']*player_ratings['Minutes']
#player_ratings['d_value'] = player_ratings['D-DPM']*player_ratings['Minutes']
player_ratings_original = player_ratings



ratings_button = st.radio('Player Ratings',('Original','Custom'))

if ratings_button =='Original':
    gb = GridOptionsBuilder.from_dataframe(player_ratings[['Team','Player','Minutes','EPM']])
    grid_options = gb.build()
    grid_response = AgGrid(player_ratings[['Team','Player','Minutes','EPM']], gridOptions=grid_options, data_return_mode='AS_INPUT', update_model='MODEL_CHANGE\D',height=350,width=750)
    player_ratings = grid_response['data']
    
else:  
    gb = GridOptionsBuilder.from_dataframe(player_ratings[['Team','Player','Minutes','EPM']])
    gb.configure_column('EPM', editable=True)
    grid_options = gb.build()
    grid_response = AgGrid(player_ratings[['Team','Player','Minutes','EPM']], gridOptions=grid_options, data_return_mode='AS_INPUT', update_model='MODEL_CHANGE\D',height=350,width=750)
    player_ratings = grid_response['data']
    
    
player_ratings['value'] = player_ratings['EPM']*player_ratings['Minutes']


team_ratings = player_ratings.groupby('Team')[['value','Minutes']].sum()
team_ratings['net_rating'] = team_ratings['value']/team_ratings['Minutes']*5


schedule = pd.read_csv('C:/Programming/Projects/nbaproject/schedule.csv')
schedule = schedule.merge(team_ratings['net_rating'],how='left',left_on='Away',right_index=True)
schedule = schedule.merge(team_ratings['net_rating'],how='left',left_on='Home',right_index=True)

schedule.columns = ['Away','Home','away_rating','home_rating']
#adding 2.7 for home court advantage from anpatton's project
schedule['home_rating'] = schedule['home_rating'] + 2.7


slider = st.slider('Simulations',0,100,5)



simulations = []
team_list = schedule.Away.unique()
standard_deviation = 9

for i in range(slider):
    winners = []
    for index, row in schedule.iterrows():
        if rnd.gauss(row['home_rating'],standard_deviation) > rnd.gauss(row['away_rating'],standard_deviation):
            winners.append(row['Home'])
        else:
            winners.append(row['Away'])
    df = pd.DataFrame(winners)
    df = df.groupby([0]).size()
    simulations.append(df)

simulations = pd.DataFrame(simulations)

conference_list = ['East','West','East','East','West','West','East','East','East','West','East','West','West','West','East','West','West','East','East','East','West','West','West','West','West','East','East','West','East','East']
teams = pd.DataFrame([team_list,conference_list]).transpose()
teams.columns = ['Team','Conference']
teams = teams.reset_index(drop=True)
seeds = simulations.transpose()
seeds['Team'] = seeds.index
new_team_list = seeds['Team'].to_list()
seeds = seeds.reset_index(drop=True)
seeds = pd.merge(seeds, teams, how='left',on='Team')
seeds = pd.DataFrame(seeds.groupby('Conference').rank('first',ascending=False))
seeds['Team'] = new_team_list
seeds = pd.merge(teams,seeds,how='left',on='Team')

def playoffScoring(team1, team2):
    game_winners = []
    for i in range(7):
        if rnd.gauss(team_ratings.loc[[team1]]['net_rating'],standard_deviation).to_list() > rnd.gauss(team_ratings.loc[[team2]]['net_rating'],standard_deviation).to_list():
            game_winners.append(team1)
        else:
            game_winners.append(team2)
    if game_winners.count(team1) > game_winners.count(team2):
        return team1
    else:
        return team2
    

def games_round(games):
    winners = []
    for team1, team2 in games:
        winning_team = playoffScoring(team1, team2) 
        winners.append(winning_team)
    return winners

def plan_games(teams):
    return zip(teams[::2], teams[1::2])


east_teams = []   
west_teams = []  
for i in range(slider):
    east_teams.append(seeds[(seeds['Conference']=='East') & (seeds[i] < 9)]['Team'].to_list())
    west_teams.append(seeds[(seeds['Conference']=='West') & (seeds[i] < 9)]['Team'].to_list())

east_teams_df = pd.DataFrame(east_teams).transpose()
west_teams_df = pd.DataFrame(west_teams).transpose()



def playoff_sim(east,west):
     round1_east = east
     games = plan_games(east)
     east = games_round(games)
     round2_east = east
     games = plan_games(round2_east)
     teams2_east = games_round(games)
     round3_east = teams2_east
     games = plan_games(round3_east)
     teams3_east = games_round(games)
     round4_east = teams3_east
     playoff_results_east = pd.DataFrame(
          {'1stRound': pd.Series(round1_east),
           '2ndRound': pd.Series(round2_east),
           'ConferenceFinals': pd.Series(round3_east),
           'Finals': pd.Series(round4_east)}
     )
     round1_west = west
     games = plan_games(west)
     west = games_round(games)
     round2_west = west
     games = plan_games(round2_west)
     teams2_west = games_round(games)
     round3_west = teams2_west
     games = plan_games(round3_west)
     teams3_west = games_round(games)
     round4_west = teams3_west
     playoff_results_west = pd.DataFrame(
          {'1stRound': pd.Series(round1_west),
           '2ndRound': pd.Series(round2_west),
           'ConferenceFinals': pd.Series(round3_west),
           'Finals': pd.Series(round4_west)}
     )
     championship_teams = round4_west + round4_east
     games = plan_games(championship_teams)
     champion = games_round(games)
     champion = pd.DataFrame(
          {'Champion': pd.Series(champion)}
     )
     frames = [playoff_results_east,playoff_results_west,champion]
     playoff_results = pd.concat(frames)
     return playoff_results

all_playoff_results = []
for i in range(slider):
    east_teams = east_teams_df[i]
    west_teams = west_teams_df[i]
    df = playoff_sim(east_teams,west_teams)
    all_playoff_results.append(df)
    

all_playoff_results_df = pd.concat(all_playoff_results)
first_round = all_playoff_results_df.groupby('1stRound').size()/slider
second_round = all_playoff_results_df.groupby('2ndRound').size()/slider
conference_finals = all_playoff_results_df.groupby('ConferenceFinals').size()/slider
finals = all_playoff_results_df.groupby('Finals').size()/slider
champions = all_playoff_results_df.groupby('Champion').size()/slider

all_playoff_results_df_list = [first_round,second_round,conference_finals,finals,champions]
all_playoff_results_df_count = pd.DataFrame(all_playoff_results_df_list).transpose()
all_playoff_results_df_count.columns = ['1stRound','2ndRound','ConferenceFinals','Finals','Champion']


summary = simulations.describe()
summary = summary.transpose()
summary = summary.merge(all_playoff_results_df_count,how='left',left_index=True,right_index=True).sort_values('Champion')
summary.index.name = 'Team'
summary = summary[['mean','min','max','1stRound','2ndRound','ConferenceFinals','Finals','Champion']]

st.dataframe(summary.sort_values('Champion'),height=750)

#st.write(plt.boxplot(simulations))







