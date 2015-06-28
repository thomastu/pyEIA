from .query import CategoryQuery, SeriesQuery

class categoryBrowser:
    """
    Creates category and series queries to make a command-line
    browsable and easily scriptable api interface.  The browser interface
    mimics the default EIA API browser.  
    """

    def __init__(self, **kwargs):
        """
        """
        self.query = CategoryQuery()

    def __str__(self):
        """
        """
        pass

    def __repr__(self):
        pass

    def browse(self, category_id):
        category_id = self._validate_category_id(category_id)
        response = self.query.get(category_id)
        self._set_response_attributes(response)

    def _validate_category_id(self, category_id):
        return str(category_id)

    def _set_response_attributes(self, response):
        attributes = ['name', 'path', 'category_id']
        for attr in attributes:
            method = "_get_{0}".format(attr)
            value = getattr(self, method)(response)
            setattr(self, attr, value)
        
    def _get_name(self, response):
        return response['category']['name']

    def _get_category_id(self, response):
        return response['category']['category_id']

    def _get_path(self, reponse, path=[]):
        category_id = self._get_category_id(response)
        parent_category_id = response['category']['parent_category_id']
        path.append(category_id)
        if category_id == '371':
            f = lambda x : self._get_name(self.query.get(x))
            path.reverse()
            return map(f, path)
        else:
            response = self.query.get(parent_category_id)
            return self._get_path(response, path)

