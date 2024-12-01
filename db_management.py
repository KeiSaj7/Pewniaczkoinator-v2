import sqlite3
import pandas as pd
import unicodedata

class DBService:

    def __init__(self):
        self.db_name = 'LeagueLeadersTable'


    def normalize_name(self, name: str) -> str:
        name = name.replace('ö', 'oe')
        name = name.replace('.', '')
        return ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        ).lower()

    # Add/refresh players stats data to db
    def Refresh_db(self, data_frame: pd.DataFrame) -> None:
        print("Refreshing the database data...")
        data_frame['NORMALIZED_PLAYER'] = data_frame['PLAYER'].apply(self.normalize_name)
        # Query to the sqlite3 db
        create_table_query = f'''    
        CREATE TABLE IF NOT EXISTS {self.db_name} (
            PLAYER_ID INTEGER PRIMARY KEY,
            RANK INTEGER,
            PLAYER TEXT,
            NORMALIZED_PLAYER TEXT,
            TEAM_ID INTEGER,
            TEAM TEXT,
            GP INTEGER,
            MIN REAL,
            FGM REAL,
            FGA REAL,
            FG_PCT REAL,
            FG3M REAL,
            FG3A REAL,
            FG3_PCT REAL,
            FTM REAL,
            FTA REAL,
            FT_PCT REAL,
            OREB REAL,
            DREB REAL,
            REB REAL,
            AST REAL,
            STL REAL,
            BLK REAL,
            TOV REAL,
            PTS REAL,
            EFF REAL
        );
        '''
        # Connect to the db
        conn, cursor = self.OpenDBConnection()
        # Create the table if doesn't exist
        cursor.execute(create_table_query)
        # Insert new data to the db
        data_frame.to_sql('LeagueLeadersTable', conn, if_exists='replace', index=False)
        # Commit and close conn
        self.CloseDBConnection(conn=conn)
        print("Database refreshed.")

    def FetchPlayerStats(self, player_name: str) -> list:
        print(f'Fetching players stats for {player_name} from the database...')
        # Leave only first_name and last_name
        player_name = player_name.split()
        player_name = f'{player_name[0]} {player_name[1]}'

        fetch_player_stats_query = f'''
        SELECT PTS, AST, REB, FG3M, STL, BLK , TOV, EFF
        FROM LeagueLeadersTable
        WHERE NORMALIZED_PLAYER LIKE ?
        '''
        conn, cursor = self.OpenDBConnection()
        cursor.execute(fetch_player_stats_query, (f'%{player_name}%',))
        db_response = cursor.fetchall()
        response = self.ProcessPlayerStatsResponse(db_response=db_response, player_name=player_name)
        print('Fetching completed.')
        self.CloseDBConnection(conn=conn)
        return response
    
    def ProcessPlayerStatsResponse(self, db_response: list, player_name: str) -> list:
        if db_response == []: 
            print('DB response is empty.')
            return
        response = {player_name:
            [{'PTS' : db_response[0][0]},
            {'AST' : db_response[0][1]},
            {'REB' : db_response[0][2]},
            {'FG3M' : db_response[0][3]},
            {'STL' : db_response[0][4]},
            {'BLK' : db_response[0][5]},
            {'TOV' : db_response[0][6]},
            {'EFF' : db_response[0][7]}
        ]}
        return response
    
    def GetPlayerID(self, player_name: str) -> int:
        # Leave only first_name and last_name
        player_name = player_name.split()   
        player_name = f'{player_name[0]} {player_name[1]}'
        normalized_player_name = self.normalize_name(player_name)
        
        fetch_player_id_query = f'''
        SELECT PLAYER_ID
        FROM LeagueLeadersTable
        WHERE NORMALIZED_PLAYER = ?
        '''
        conn, cursor = self.OpenDBConnection()
        cursor.execute(fetch_player_id_query, (normalized_player_name,))
        db_response = cursor.fetchone()
        self.CloseDBConnection(conn=conn)
        return db_response
    
    def GetPlayerMinutes(self, player_name: str) -> float:
        # Leave only first_name and last_name
        player_name = player_name.split()   
        player_name = f'{player_name[0]} {player_name[1]}'
        normalized_player_name = self.normalize_name(player_name)

        fetch_player_minutes_query = f'''
        SELECT MIN
        FROM LeagueLeadersTable
        WHERE NORMALIZED_PLAYER LIKE ?
        '''
        conn, cursor = self.OpenDBConnection()
        cursor.execute(fetch_player_minutes_query, (normalized_player_name,))
        db_response = cursor.fetchone()
        self.CloseDBConnection(conn=conn)
        return db_response

    def GetTeamID(self, player_name: str) -> int:
        # Leave only first_name and last_name
        print(player_name)
        player_name = player_name.split()   
        player_name = f'{player_name[0]} {player_name[1]}'
        normalized_player_name = self.normalize_name(player_name)
        
        fetch_player_id_query = f'''
        SELECT TEAM_ID
        FROM LeagueLeadersTable
        WHERE NORMALIZED_PLAYER = ?
        '''
        conn, cursor = self.OpenDBConnection()
        cursor.execute(fetch_player_id_query, (normalized_player_name,))
        db_response = cursor.fetchone()
        self.CloseDBConnection(conn=conn)
        return db_response
    
    def OpenDBConnection(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        return conn,cursor
    
    def CloseDBConnection(self, conn: sqlite3) -> None:
        conn.commit()
        conn.close()
