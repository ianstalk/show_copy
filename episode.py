import re, os, shutil, rarfile
from rarfile import is_rarfile
 
ARTICLES = ['a', 'an', 'of', 'the', 'is']
PROPER_PATTERNS = ['proper', 'repack']
SAMPLE_PATTERNS = ['sample']
 
class InvalidEpisode(ValueError):
    pass
 
class Episode(object):
    def __init__(self, file):
 
        # assign args to variables
        self.file = file
        
        # initialize variables
        self.show = ""
        self.season = 0
        self.episode = 0
        self.extension = file.split('.')[-1].lower()
        self.is_sample = self._in_filename(SAMPLE_PATTERNS)
        self.is_proper = self._in_filename(PROPER_PATTERNS)
 
        # private variables
        self._ep_string = ""
 
        self._parse_episode()
 
    def __str__(self):
        '''Create the string representation of this episode'''
        return " ".join([self.show, self._ep_string])

    def __repr__(self):
        '''Create the canonical representation of this episode'''
        return "Episode('file'='%s')" % self.file
 
    def _title_case(self, title):
        '''converts a space delimited string into title case'''
       
        words = title.split()
        final = [words[0].capitalize()]
        for word in words[1:]:
           final.append(word in ARTICLES and word or word.capitalize())
 
        return " ".join(final)

    def _in_filename(self, patterns):
        '''returns True if any element of patterns is a 
        substring of self.file'''

        lowerfile = self.file.lower()
        return any(patt.lower() in lowerfile for patt in patterns)

    def _invalid_episode(self):
        '''Raise an InvalidEpisode error'''

        err_str = ' '.join(('Not a valid episode:', self.file))
        raise InvalidEpisode(err_str)
 
    def _parse_episode(self):
        '''parses file names into show, season, and episode'''
 
        cleaned = re.sub(pattern = r'[\._]', repl = ' ', string =  self.file, \
            flags = re.IGNORECASE)
        match = re.search(pattern = r'(.*)s([0-9]+)e([0-9]+)', \
            string = cleaned, flags = re.IGNORECASE)
        
        if match:
            self.show = self._title_case(match.group(1))
            self.season = int(match.group(2))
            self.episode = int(match.group(3))
 
            self._ep_string = 's%02ie%02i' % (self.season, self.episode)
        else:
            self._invalid_episode()
 
    def episode_path(self, base_dir):
        '''Return the path where the file is expected to be copied'''

        return os.path.join(base_dir, self.show, 'Season ' + str(self.season))
 
    def _make_path(self, base_dir):
        '''Create a directory under base_dir for the show 
        and season of this episode'''
 
        new_path = self.episode_path(base_dir)
        
        if not os.path.exists(new_path):
            os.makedirs(new_path)
 
        return new_path
 
class EpisodeFile(Episode):
    '''Implements basic file functionality for the Episode class'''
 
    def __init__(self, path):
        
        self.path = path
        file = self._get_filename()

        super(EpisodeFile, self).__init__(file)

    def _invalid_file(self):
        '''Raise an InvalidEpisode error'''

        err_str = ' '.join(('Not a valid file:', self.path))
        raise InvalidEpisode(err_str)

    def _get_filename(self):
        '''Get the filename of the provided path'''

        if not os.path.isfile(self.path):
            self._invalid_file()

        return os.path.basename(self.path) 
 
    def put_file(self, base_dir):
        '''copies the episode from its current location to its proper location 
        under base_dir. returns True if file copy is successful'''
 
        new_path = self._make_path(base_dir)
        new_filepath = os.path.join(new_path, self.file)
        copied = False
 
        if not os.path.exists(new_filepath):
            shutil.copy(self.path, new_filepath)
            copied = True

        return copied

    def del_file(self):
        '''deletes the file located at the provided path'''
 
        if os.path.exists(self.path):
            os.remove(self.path)
 
class EpisodeRar(Episode):
    '''Implements RAR functionality for the Episode class'''
 
    def __init__(self, path):

        self.path = path
        self._open_rar()
        file = self._get_filename()
 
        # now that we've found the file name we can initialize the
        # superclass
        super(EpisodeRar, self).__init__(file)
 
    def _invalid_rar(self):
        '''Raise an InvalidEpisode error'''

        err_str = ' '.join(('Not a valid RAR:', self.path))
        raise InvalidEpisode(err_str)

    def _open_rar(self):
        '''Create a new RAR object'''

        try:
            self._rar =  rarfile.RarFile(self.path)
            self._rar.testrar()
        except rarfile.NeedFirstVolume:
            self._invalid_rar()

        return self._rar
 
    def _get_filename(self):
        '''Gets the filename of the episode, assuming the largest file in the
        RAR is the one we want'''
 
        return max(self._rar.infolist(), key=lambda f: f.file_size).filename
 
    def put_file(self, base_dir):
        '''extracts the episode into its proper location under base_dir
        returns true if extraction is successful'''
 
        new_path = self._make_path(base_dir)
        fullpath = os.path.join(new_path, self.file)
        copied = False
 
        if not os.path.exists(fullpath):
            self._rar.extract(self.file, new_path)
 
            copied = True

        return copied

    def del_file(self):
        '''deletes the rar and all associated rar volumes'''
        volumes = self._rar.volumelist()
        self._rar.close()

        for volume in volumes:
            os.remove(volume)
            


def get_episode(path):
    '''Return the appropriate Episode implementation based on the file type'''

    episode = None
    extension = path.split('.')[-1].lower()

    is_rar = bool(re.search(pattern = r'rar|r\d{2,3}', \
             string = extension, flags = re.IGNORECASE))

    if is_rar:
        episode = EpisodeRar(path)
    else:
        episode = EpisodeFile(path)

    return episode
