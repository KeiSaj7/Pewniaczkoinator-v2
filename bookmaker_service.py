import requests
from datetime import datetime, timedelta
from db_management import DBService
import pandas as pd

class BookmakerService:

    def __init__(self, db_manager: DBService, nba_service):
        self.api_key = 'API_KEY'
        self.db_manager = db_manager
        self.nba_service = nba_service
        self.stats_hashmap = {
            'player_points' : 'PTS',
            'player_rebounds' : 'REB',
            'player_assists' : 'AST',
            'player_threes' : 'FG3M',
            'player_blocks' : 'BLK',
            'player_steals' : 'STL',
            'player_turnovers' : 'TOV',
        }
        self.combined_stats_mapping = {
            'player_points_rebounds_assists': ['PTS', 'REB', 'AST'],
            'player_points_rebounds': ['PTS', 'REB'],
            'player_points_assists': ['PTS', 'AST'],
            'player_rebounds_assists': ['REB', 'AST']
        }
        
    # Main method combining all data into data frame
    def CombineData(self):
        combined_data = []
        # Get data from bookmaker
        bookmaker_data = self.Get_today_matches_ids()
        # Create data frame (Get_today_matches_ids + FetchPlayerGames + FetchPlayerStats)
        # PLAYER / MARKET / TYPE(Over/Under) / LINE / ODDS / ACHIEVED / AVERAGE
        for match in bookmaker_data:
            for match, player in match.items():
                for player, markets in player.items():
                    average_stats = self.db_manager.FetchPlayerStats(player_name=player)
                    player_role = self.PlayerRole(player_name=player)
                    if average_stats is None or player_role is None: continue
                    average_stats = average_stats[player]
                    print(average_stats)
                    player_games = self.nba_service.FetchPlayerGames(player_name=player)
                    injured_games = self.nba_service.ChekcIfInjured(player_name=player)
                    home_or_away = self.nba_service.HomeOrAway(player_name=player)
                    plus_minus = self.nba_service.GetPlayerPlusMinus(player_games)
                    for market, line in markets.items():
                        if market in self.stats_hashmap.keys():
                            key = self.stats_hashmap[market]
                            average_stat = next((stat[key] for stat in average_stats if key in stat ), 0)
                            print(average_stat)
                        else:
                            # sum of stats
                            keys = self.combined_stats_mapping[market]
                            average_stat = 0
                            for key in keys:
                                stat = next((stat[key] for stat in average_stats if key in stat ), 0)
                                average_stat += stat
                        for line, bet_type in line.items():
                            last_five_games = self.RecentPerformance(n_games=5, player_games=player_games, market=market, line=line)
                            last_ten_games = self.RecentPerformance(n_games=10, player_games=player_games, market=market, line=line)
                            achieved, games_played = self.LinesAchieved(player_games=player_games, market=market, line=line)
                            for bet_type, odds in bet_type.items():
                                if odds == None: continue
                                combined_data.append({
                                    'MATCH' : match,
                                    'PLAYER' : player,
                                    'MARKET' : market,
                                    'TYPE' : bet_type,
                                    'LINE' : line,
                                    'ODDS' : odds,
                                    'ACHIEVED' : f'{games_played-achieved}/{games_played}' if bet_type == 'Under' else f'{achieved}/{games_played}',
                                    'ACHIEVED[%]' : round(((games_played-achieved)/len(player_games))*100,2) if bet_type == 'Under' else round((achieved/len(player_games))*100,2),
                                    'AVERAGE' : average_stat,
                                    'LAST 5 GAMES' : f'{last_five_games[0]}/{last_five_games[1]}' if bet_type == 'Over' else f'{(last_five_games[1]-last_five_games[0])}/{last_five_games[1]}',
                                    'LAST 10 GAMES' : f'{last_ten_games[0]}/{last_ten_games[1]}' if bet_type == 'Over' else f'{(last_ten_games[1]-last_ten_games[0])}/{last_ten_games[1]}',
                                    'AVG_MINUTES' : player_role[0],
                                    'IS_STARTER' : player_role[1],
                                    'EFFICIENCY' : average_stats[7]['EFF'],
                                    'PLUS_MINUS' : plus_minus,
                                    'RECENTLY_INJURED' : f'{injured_games}/5',
                                    'HOME/AWAY' : home_or_away
                                })
        # Create DataFrame                            
        df = pd.DataFrame(combined_data)
        df = df.sort_values(by='ACHIEVED[%]', ascending=False)
        # Save to excel
        df.to_excel('output.xlsx', index=False)
        print(df)
                        
        
    # Fetch today's matches and their ids
    def Get_today_matches_ids(self) -> list:
        print('Fetching today\'s matches...')
        today_datetime = datetime.now().isoformat(timespec='seconds') + 'Z'
        tommorow_datetime = (datetime.now() + timedelta(hours=24)).isoformat(timespec='seconds') + 'Z'
        params = {  
            'apiKey' : self.api_key,
            'commenceTimeFrom' : today_datetime,
            'commenceTimeTo' : tommorow_datetime
        }
        try:
            response = requests.get('https://api.the-odds-api.com/v4/sports/basketball_nba/events', params=params) 
            response.raise_for_status()
            matches = response.json()
            # Get matche's ids
            matches_ids = []
            for match in matches:
                matches_ids.append(match['id'])
            print('Fetched ids for today\'s matches.')
            return self.Get_matches_odds(matches_ids)
        except requests.exceptions.RequestException as e:
            print(f'Failed fetching today\'s matches: {e}')
            return []   

    def Get_matches_odds(self, matches_ids: list):
        print('Fetching odds for today\'s mathces...')
        params = {
            'apiKey' : self.api_key,
            'regions' : 'us',
            'markets' : 'player_points,player_rebounds,player_assists,player_threes,player_points_rebounds_assists,player_points_rebounds,player_points_assists,player_rebounds_assists,player_blocks,player_steals,player_turnovers',
            'oddsFormat' : 'decimal',
        }
        # Fetch odds for every match
        result = []
        for id in matches_ids:
            try:
                response = requests.get(f'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{id}/odds', params=params)
                #response = requests.get(f'https://api.the-odds-api.com/v4/sports/basketball_nba/events/{matches_ids[0]}/odds', params=params)
                bookmaker_data = response.json()
                data = self.Fetch_bets_info(bookmaker_data)
                result.append(data)
            except requests.exceptions.RequestException as e:
                print(f'Failed fetching odds for today\'s matches: {e}')
                return
        return result

    def Fetch_bets_info(self, bookmaker_data : list) -> list:
        bet_match_info = f"{bookmaker_data['home_team']} vs {bookmaker_data['away_team']}"
        match_bets_data = {}
        for bookmaker in bookmaker_data['bookmakers']:
            for market in bookmaker['markets']:
                bet_key = market['key']
                for outcome in market['outcomes']:
                    # {'name': 'Under', 'description': 'Zach LaVine', 'price': 1.68, 'point': 3.5}
                    # Fetch the data from dict structured like above
                    if outcome['name'] != 'Over' and outcome['name'] != 'Under':
                        continue
                    bet_type = outcome['name']
                    if outcome['price'] < 3 and outcome['price'] > 1.5 :
                        bet_odd = outcome['price']
                    else: 
                        continue 
                    bet_player = self.db_manager.normalize_name(outcome['description'])
                    bet_line = outcome['point']

                    if bet_match_info not in match_bets_data:
                        match_bets_data[bet_match_info] = {}
                    if bet_player not in match_bets_data[bet_match_info]:
                        match_bets_data[bet_match_info][bet_player] = {}
                    if bet_key not in match_bets_data[bet_match_info][bet_player]:
                        match_bets_data[bet_match_info][bet_player][bet_key] = {}
                    if bet_line not in match_bets_data[bet_match_info][bet_player][bet_key]:
                        match_bets_data[bet_match_info][bet_player][bet_key][bet_line] = {'Over' : None, 'Under' : None}
                    match_bets_data[bet_match_info][bet_player][bet_key][bet_line][bet_type] = bet_odd
                    
        return match_bets_data
    
    '''
     /////// FACTOR METHODS ///////
    '''

    # Get stats averages only for players who are in event odds
    def GetPlayersStats(self, match_bets_data: list):
        players_stats = []
        for match, players in match_bets_data.items(): 
            for player,markets in players.items():
                players_stats.append(self.db_manager.FetchPlayerStats(player))
        return players_stats

    # Count how many times player achieved the line
    def LinesAchieved(self, player_games: pd.DataFrame, market: str, line: float):
        if market in self.combined_stats_mapping.keys():
            return self.LinesAchievedForMultiStats(player_games=player_games, market=market, line=line)
        market = self.stats_hashmap[market]
        game_stat = player_games[market].tolist()
        achieved = 0
        for game in game_stat:
            if game > line:
                achieved += 1
        print(f'Achieved (for {market} | line {line}): {achieved}/{len(game_stat)} | {round((achieved/len(player_games))*100,2)}%')
        return achieved, len(game_stat)

    def LinesAchievedForMultiStats(self, player_games: pd.DataFrame, market: str, line: float):
        stats_columns = self.combined_stats_mapping[market]
        achieved = 0
        for _, row in player_games.iterrows():
            combined_stat = sum(row[stat] for stat in stats_columns)
            if combined_stat > line:
                achieved += 1
        print(f'Achieved (for {market} | line {line}): {achieved}/{len(player_games)} | {round((achieved/len(player_games))*100,2)}%')
        return achieved, len(player_games)

    # Get stats for last n games
    def RecentPerformance(self, n_games: int, player_games: pd.DataFrame, market: str, line: float):
        last_5_games = player_games.head(n_games)
        return self.LinesAchieved(player_games=last_5_games, market=market, line=line)
    
    # Determine if player is a starter or not
    def PlayerRole(self, player_name: str):
        # Assume that starters play more than 24 minutes
        player_minutes: float = self.db_manager.GetPlayerMinutes(player_name=player_name)
        if player_minutes is None: return None
        is_starter: bool = player_minutes[0] > 24
        return player_minutes[0], is_starter