from bs4 import BeautifulSoup
import difflib
import requests
from urllib.request import urlopen



class RTScraper:
    BASE_URL = "https://www.rottentomatoes.com/api/private/v2.0"
    SEARCH_URL = "{base_url}/search".format(base_url=BASE_URL)

    def __init__(self):
        self.metadata = dict()
        self.url = None

    def extract_url(self):
        pass

    def extract_metadata(self, **kwargs):
        pass

    def _extract_section(self, section):
        pass

    @staticmethod
    def search(term, limit=10):
        r = requests.get(url=RTScraper.SEARCH_URL, params={"q": term, "limit": limit})
        r.raise_for_status()
        return r.json()


class MovieScraper(RTScraper):
    def __init__(self, **kwargs):
        RTScraper.__init__(self)
        self.movie_genre = None
        if 'movie_title' in kwargs.keys():
            self.movie_title = kwargs['movie_title']
            self.extract_url()
        if 'movie_url' in kwargs.keys():
            self.url = kwargs['movie_url']

    def extract_url(self):
        search_result = self.search(term=self.movie_title)

        movie_titles = []
        for movie in search_result['movies']:
            movie_titles.append(movie['name'])

        closest = self.closest(self.movie_title, movie_titles)

        url_movie = None
        for movie in search_result['movies']:
            if movie['name'] == closest[0]:
                url_movie = 'https://www.rottentomatoes.com' + movie['url']

        self.url = url_movie

    def extract_metadata(self, columns=('Rating', 'Genre', 'Box Office', 'Studio')):
        movie_metadata = dict()
        page_movie = urlopen(self.url)
        soup = BeautifulSoup(page_movie, "lxml")

        # Score
        score = soup.find('score-board')
        movie_metadata['Score_Rotten'] = score.attrs['tomatometerscore']
        movie_metadata['Score_Audience'] = score.attrs['audiencescore']

        amountreviews = soup.find()


    @staticmethod
    def closest(keyword, words):
        closest_match = difflib.get_close_matches(keyword, words, cutoff=0.6)
        return closest_match

