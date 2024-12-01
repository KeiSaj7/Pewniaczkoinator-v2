from nba_api.stats.endpoints import leagueleaders, PlayerGameLog, TeamGameLog, PlayerNextNGames, BoxScoreTraditionalV3
from db_management import DBService
import pandas as pd
import time


class NBAService:

    def __init__(self, db_manager: DBService, bookmaker_manager):
        self.db_manager = db_manager
        self.bookmaker_manager = bookmaker_manager


    # Fetch all players stats from current season (2024-2025)
    def FetchAllPlayers(self):
        leagueleaders_request = leagueleaders.LeagueLeaders(per_mode48='PerGame', season='2024-25', season_type_all_star='Regular Season', stat_category_abbreviation='PTS')
        leagueleaders_data = leagueleaders_request.get_data_frames()[0]
        self.db_manager.Refresh_db(leagueleaders_data)
        time.sleep(1)
    
    # Fetch player's games
    def FetchPlayerGames(self, player_name: str) -> pd.DataFrame:
        print(f'{player_name} achieved:')
        player_id = self.db_manager.GetPlayerID(player_name=player_name)[0]
        player_games = PlayerGameLog(player_id=player_id).get_data_frames()[0]
        time.sleep(1)
        return player_games
    
    # Get average +/- for player
    def GetPlayerPlusMinus(self, player_games: pd.DataFrame) -> float:
        plus_minus = round(player_games['PLUS_MINUS'].mean(),1)
        time.sleep(1)
        return plus_minus

    # Fetch player's team games
    def FetchTeamGames(self, player_name: str) -> pd.DataFrame:
        team_id = self.db_manager.GetTeamID(player_name=player_name)[0]
        team_games = TeamGameLog(team_id=team_id).get_data_frames()[0]
        time.sleep(1)
        return team_games
    
    # Check if player was injured in last 5 games
    def ChekcIfInjured(self, player_name: str) -> int:
        player_games = self.FetchPlayerGames(player_name=player_name)
        team_games = self.FetchTeamGames(player_name=player_name)

        player_games_ids = player_games['Game_ID']
        team_games_ids = team_games['Game_ID']
        last_five_team_games = team_games_ids[:5].to_list()
        last_five_player_games = player_games_ids[:5]
        games_played = 0
        for game_id in last_five_player_games:
            if game_id in last_five_team_games:
                games_played += 1
        print(f'{player_name} played {games_played} games in last 5 games.')
        time.sleep(1)
        return 5-games_played

    # Home or away game
    def HomeOrAway(self, player_name: str) -> str:
        player_id = self.db_manager.GetPlayerID(player_name=player_name)[0]
        next_games = PlayerNextNGames(player_id=player_id).get_data_frames()[0]
        team_id = self.db_manager.GetTeamID(player_name=player_name)
        home_team_id = next_games['HOME_TEAM_ID'][0]
        time.sleep(1)
        if team_id == home_team_id:
            return 'Home'
        return 'Away'