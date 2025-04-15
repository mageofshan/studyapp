import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import re
import json
import urllib.parse

#insipirations from bguliano/quizlet-parser

class get_flashcards(dict):
    def __init__(self, source):
        super(get_flashcards, self).__init__()
        
        # check if source is a URL or direct input
        if source.startswith('http://') or source.startswith('https://'):
            self._parse_from_url(source)
        else:
            self._parse_from_text(source)
    
    def _parse_from_url(self, url):
        try:
            # check if it's a Quizlet URL (preferred)
            if 'quizlet.com' in url:
                self._parse_quizlet(url)
            else:
                # generic web scraper for other sites
                self._parse_generic_site(url)
                
        except Exception as e:
            # if all else fails, add a sample flashcard
            self["Error loading flashcards"] = f"Could not load from URL: {str(e)}"
            self["Sample Term"] = "Sample Definition"
    
    def _parse_quizlet(self, url):
        try:
            session = HTMLSession()
            response = session.get(url)
            soup = BeautifulSoup(response.content, features='html.parser')

            # extracting the title, author, and description
            title = soup.find('h1', {'class': re.compile('UIHeading.*one')})
            self.title = title.text if title is not None else "Untitled Set"

            author = soup.find('span', {'class': re.compile('UserLink-username')})
            self.author = author.text if author is not None else "Unknown Author"

            description = soup.find('div', {'class': re.compile('SetPageHeader-description')})
            self.description = description.text if description is not None else ""

            # extracting the flashcards
            results = soup.findAll('span', {'class': re.compile('TermText notranslate')})
            
            # fallback if the primary selector doesn't work
            if not results:
                # try alternate tags
               results = soup.findAll(['span', 'div'], {'class': re.compile('.*erm.*ext.*')})
            
            # process results
            if results:
                # double increment to get key value pairs
                for i in range(0, len(results), 2):
                    if i + 1 < len(results):
                        term = self._parse_tag_text(results[i])
                        definition = self._parse_tag_text(results[i + 1])
                        if term and definition:
                            self[term] = definition
            
            # if no flashcards were found, add some sample ones
            if len(self) == 0:
                self["Sample Term 1"] = "Sample Definition 1"
                self["Sample Term 2"] = "Sample Definition 2"
        # all failsafe       
        except Exception as e:
            self["Error loading Quizlet"] = f"Could not parse Quizlet: {str(e)}"
            self["Sample Term"] = "Sample Definition"

    def _parse_generic_site(self, url):
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # look for common flashcard patterns
                
                # try to find tables
                tables = soup.find_all('table')
                if tables:
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            # if more than two columns of info for row, first 2 are term and definition
                            if len(cells) >= 2:
                                term = cells[0].get_text().strip()
                                definition = cells[1].get_text().strip()
                                # if term and definition found, add to dictionary
                                if term and definition:
                                    self[term] = definition
                
                # try to find definition lists
                dl_lists = soup.find_all('dl')
                if dl_lists:
                    for dl in dl_lists:
                        dts = dl.find_all('dt')
                        dds = dl.find_all('dd')
                        for i in range(min(len(dts), len(dds))):
                            # dl titles and dl descriptions for term and definition
                            term = dts[i].get_text().strip()
                            definition = dds[i].get_text().strip()
                            # if term and definition found, add to dictionary
                            if term and definition:
                                self[term] = definition
                
                # if no flashcards were found, add some sample ones
                if len(self) == 0:
                    self["Sample Term 1"] = "Sample Definition 1"
                    self["Sample Term 2"] = "Sample Definition 2"
            
            # all failsafe        
            except Exception as e:
                self["Error loading website"] = f"Could not parse website: {str(e)}"
                self["Sample Term"] = "Sample Definition"

    def _parse_from_text(self, text):
            # try to parse as JSON first
            try:
                data = json.loads(text)
                for term, definition in data.items():
                    self[term] = definition
                return
            except:
                pass
            
            # try to parse line by line (term:definition format)
            lines = text.strip().split('\n')
            for line in lines:
                # skip empty lines
                if not line.strip():
                    continue
                    
                # look for separator characters
                for sep in [':', '-', '=', '\t']:
                    if sep in line:
                        parts = line.split(sep, 1)
                        term = parts[0].strip()
                        definition = parts[1].strip()
                        # if term and definition found, add to dictionary
                        if term and definition:
                            self[term] = definition
                            break
            
            # if no flashcards were parsed, add some sample ones
            if len(self) == 0:
                # try to parse as plain text paragraphs
                paragraphs = text.split('\n\n')
                if len(paragraphs) >= 2:
                    for i in range(0, len(paragraphs), 2):
                        if i + 1 < len(paragraphs):
                            self[f"Paragraph {i//2 + 1}"] = paragraphs[i+1].strip()
                else:
                    self["Sample Term 1"] = "Sample Definition 1"
                    self["Sample Term 2"] = "Sample Definition 2"

    @staticmethod
    def _parse_tag_text(tag) -> str:
        # if nothing found, return empty string
        if not tag:
            return ""

        #empty string    
        result = ''
        for item in tag.contents:
            # if string and not a tag, add to result
            if isinstance(item, str):
                result += item
            # if tag, result is not empty, and last char is not newline, add newline
            elif len(result) and result[-1] != '\n':
                result += '\n'
        # return polished string
        return result.strip()

# Example usage
# url = "https://quizlet.com/9607765/ap-us-history-ch-4-flash-cards/
# flashcards = get_flashcards(url)
# print(flashcards)