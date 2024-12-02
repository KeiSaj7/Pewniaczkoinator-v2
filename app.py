import flask
import pandas as pd
from NBA_service import NBAService
from db_management import DBService
from bookmaker_service import BookmakerService

class App(flask.Flask):
    def __init__(self, *args, **kwargs):
        self.db_manager = kwargs.get('db_manager', DBService())
        self.bookmaker_service = kwargs.get('bookmaker_service', BookmakerService(db_manager=self.db_manager, nba_service=None))
        self.nba_service = kwargs.get('nba_service', NBAService(db_manager=self.db_manager, bookmaker_manager=self.bookmaker_service))
        self.bookmaker_service.nba_service = self.nba_service
        super(App, self).__init__(*args, **kwargs)
        self.config['SECRET_KEY'] = 'SECRET_KEY'
        self.setup_routes()

    def setup_routes(self):
        @self.route('/')
        def index():
            return flask.render_template('index.html')
    
        @self.route('/fetch_data', methods=['POST'])
        def fetch_data():
            self.nba_service.FetchAllPlayers()
            self.bookmaker_service.CombineData()
            return flask.redirect(flask.url_for('show_data'))

        @self.route('/show_data')
        def show_data():
            page = int(flask.request.args.get('page', 1))
            rows_per_page = 10
            df = pd.read_excel('output.xlsx')
            total_pages = (len(df) - 1) // rows_per_page + 1
            start = (page - 1) * rows_per_page
            end = start + rows_per_page
            df_page = df.iloc[start:end]
            html_table = df_page.to_html(classes='table table-responsive table-striped table-hover table-bordered', index=False)
            html_table = html_table.replace('<th>', '<th class="text-center align-middle">')
            html_table = html_table.replace('<td>', '<td class="text-center align-middle">')
            return flask.render_template('data.html', table=html_table, page=page, total_pages=total_pages, max=max, min=min)
        
if __name__ == "__main__":
    app = App(__name__)
    app.run(debug=True)