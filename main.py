from NBA_service import NBAService
from db_management import DBService
from bookmaker_service import BookmakerService

if __name__ == "__main__":
    # Create instances
    db_manager = DBService()
    bookmaker_service = BookmakerService(db_manager=db_manager, nba_service=None)
    nba_service = NBAService(db_manager=db_manager, bookmaker_manager=bookmaker_service)
    bookmaker_service.nba_service = nba_service
    # Main logic
    nba_service.FetchAllPlayers()
    bookmaker_service.CombineData()