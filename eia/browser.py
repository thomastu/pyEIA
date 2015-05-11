from .query import CategoryQuery, SeriesQuery

class browser:
    """
    Creates category and series queries to make a command-line
    browsable and easily scriptable api interface.  The browser interface
    mimics the default EIA API browser.  
    """

    def __init__(self, **kwargs):
        """
        ---------- Optional Arguments ----------
        """

        self.category = CategoryQuery()
        self.series = SeriesQuery()
        self.silent = kwargs.get('silent', True)
        self.category_ids = {}
        self.series_ids = {}
        self.flags = []
        self.display_menu(silent = self.silent)

    def __str__(self):
        """
        """
        return 

    def __repr__(self):
        base = '<EIA Browser : {s}>'
        return base.format(s = str(self))

    def display_menu(self):
        """
        
        """
        pass 

    def create_menu(self):
        """
        """
        r = self.response 
        prompt = \
        '\nPlease select a {qtype} from {name} (ID : {id} ) : \n\n'.format(\
            qtype = query_type, 'name' = self.category_name, 'id'  = self.category_id)