
import os
import re
from datetime import datetime
from collections import defaultdict

from lxml import etree

from utils import TIME_SLICE_EVENTS
import utils

# regexes
TS = '(\d+)[^\d]+(\d+)'
LOC = '([\d\.]+)[^\d]+([\d+\.]+)'
COMP_ID = '(.*)_(\d+).xml'

# attr types
COORS = ('loc', 'start', 'middle', 'end')
BOOLS = ('shot', 'long_ball', 'headed', 'assists', 'through_ball', 'is_own')
FLOATS = ('x', 'y', 'x_loc', 'gx', 'gy', 'y_loc', 'bmi')
INTS = ('mins', 'minsec', 'secs', 'weight', 'height', 'shirt_num', 'age')
DATES = ('dob',)

# xpaths
EVENTS = '/squawka/data_panel/filters/{}/time_slice/event'
TEAM = '/squawka/data_panel/game/team[@id="{}"]'
PLAYER = '/squawka/data_panel/players/player[@id="{}"]'
HOME = '/squawka/data_panel/game/team[state = "home"]'
AWAY = '/squawka/data_panel/game/team[state = "away"]'
GOAL = '/squawka/data_panel/filters/goals_attempts' + \
       '/time_slice/event[@type="goal" and @team_id="{}"]'
POSSESION = '/squawka/data_panel/possession/period/' + \
            'time_slice[@name="{}"]/team_possession[@team_id="{}"]/text()'
POSSESION_IJP = '/squawka/data_panel/possession/period/' + \
                'time_slice[@name="{}"]/team_possession[@team_id="{}"]/text()'

# team_id
ID_TEAM_ID = ('goal_keeping', 'goals_attempts', 'headed_duals',
              'interceptions', 'clearances', 'all_passes')
ID_TEAM = ('tackles', 'crosses', 'corners', 'keepersweeper',
           'setpieces', 'offside')


def _parse_node(node, **kwargs):
    # attributes
    attrs = {k: _parse_attr(k, v) for k, v in node.attrib.items()}
    # children
    children = {}
    for c in node.getchildren():
        for k, v in [(c.tag, c.text)] + list(c.attrib.items()):
            c_key = c.tag + '_' + k if k in c.attrib else k
            children[c_key] = _parse_attr(k, v)
    return {**attrs, **children, **kwargs}


def _parse_attr(attr_key, attr_val, verbose=False):
    if attr_key in COORS:
        x, y = re.match(LOC, attr_val).groups()
        return {'x': float(x), 'y': float(y)}
    elif attr_key in BOOLS:
        if attr_val == 'true' or attr_val == 'yes':
            return True
        else:
            assert attr_val == 'false'
            return False
    elif attr_key in FLOATS:
        return float(attr_val)
    elif attr_key in INTS:
        return int(attr_val)
    elif attr_key in DATES:
        return datetime.strptime(attr_val, '%d/%m/%Y')
    else:
        if verbose:
            print("Not parsing ", attr_key, attr_val)
        return attr_val


def _flip_loc(e):
    if 'start' in e or 'end' in e:
        e['start']['x'] = 100 - e['start']['x']
        e['start']['y'] = 100 - e['start']['y']
        e['end']['x'] = 100 - e['end']['x']
        e['end']['y'] = 100 - e['end']['y']
    if 'loc' in e:
        e['loc']['x'] = 100 - e['loc']['x']
        e['loc']['y'] = 100 - e['loc']['y']
    return e


def _maybe_flip(ftype, e, team_id):
    """Some events seem to refer to the event coordinates with respect to the
    opposite team. This function is a heuristic to find out which cases ought
    to be unflipped"""
    if utils.get_team_id(e) != team_id:
        return _flip_loc(e)
    elif ftype == 'tackles' and e['tackler_team'] != team_id:
        return _flip_loc(e)
    elif ftype == 'fouls' and e['otherplayer_team'] == team_id:
        return _flip_loc(e)
    return e


class SquawkaMatch(object):
    """
    Class wrapping a squawka xml for easy access.
    """
    def __init__(self, path_or_string, path=None):
        self._cache = defaultdict(lambda: defaultdict(dict))
        if os.path.isfile(path_or_string):
            self.path = path_or_string
            with open(path_or_string, 'r') as f:
                self.xml = etree.fromstring(bytes(f.read(), 'utf'))
        else:
            if path is None:
                raise ValueError("String input needs optional path")
            self.path = path
            self.xml = etree.fromstring(bytes(path_or_string, 'utf'))

    @classmethod
    def search(cls, dirpath, team1, team2, competition,
               team_prop='short_name'):
        for f in os.listdir(dirpath):
            if f.startswith(competition):
                m = cls(os.path.join(dirpath, f))
                h, a = m.team_home[team_prop], m.team_away[team_prop]
                if (h == team1 and a == team2) or (a == team1 and h == team2):
                    yield m

    def __getattr__(self, name):
        if name in TIME_SLICE_EVENTS:
            return self._get_filter_events(name)
        else:
            msg = "'{}' object has no attribute '{}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    def __repr__(self):
        date = self.kickoff.strftime('%a %d/%m/%y')
        home, away = self.score
        return '{} [{}-{}]; {}; {}'.format(
            self.name, home, away, self.competition, date)

    def _get_filter_events(self, filter_type):
        events, elements = [], self.xml.xpath(EVENTS.format(filter_type))
        if elements is not None:
            for e in elements:
                # parent (timeslice)
                ts0, ts1 = re.match(TS, e.getparent().attrib['name']).groups()
                ts = {'timeslice': {'from': int(ts0), 'to': int(ts1)}}
                events.append(_parse_node(e, ts=ts))
        return events

    def get_timed_events(self):
        """Return events with time information"""
        for f in self.filters:
            try:
                for event in getattr(self, f):
                    if 'mins' in event and 'secs' in event:
                        yield f, event
            except AttributeError:
                continue

    def get_attempts(self, filter_goals=False, breaks=1):
        """
        Return a list of tuples (event_type, {event}) that lead to
        a goal attempt.

        Parameters:
        -----------
        filter_goals: bool, whether to filter for goal events
        breaks: int (default = 1), maximum number ball possession
            changes to include in the returned event.
        """
        events = list(self.get_timed_events())
        events = sorted(events, key=lambda e: (e[1]['mins'], e[1]['secs']))
        for idx, (ftype, e) in enumerate(events):
            if ftype == 'goals_attempts':
                # filter goals if argument passed
                if filter_goals and e['type'] != 'goal':
                    continue
                team_id = utils.get_team_id(e)
                attempt, ctx_idx, ctx_breaks = [], idx - 1, 0
                while ctx_idx > 0:
                    ctx_ftype, ctx_e = events[ctx_idx]
                    ctx_breaks += utils.get_team_id(ctx_e) != team_id
                    # break on overlapping attempts or possesion change
                    if ctx_ftype == 'goals_attempts' or ctx_breaks > breaks:
                        break
                    # skip extra heat maps
                    elif ctx_ftype == 'extra_heat_maps':
                        ctx_idx -= 1
                        continue
                    # skip unlocated or irrelevant events
                    elif not utils.is_loc(ctx_e):
                        ctx_idx -= 1
                        continue
                    # record the event
                    else:
                        # flip if event belongs to other team
                        ctx_e = _maybe_flip(ctx_ftype, ctx_e, team_id)
                        attempt.append((ctx_ftype, ctx_e))
                        ctx_ftype, ctx_e = events[ctx_idx]
                        ctx_idx -= 1
                yield attempt[::-1] + [(ftype, e)]

    def _background_info(self):
        goals_home, goals_away = self.score
        return {'competition': self.competition,
                'match': self.match_id,
                'kickoff': self.kickoff,
                'team_home': self.team_home['id'],
                'team_away': self.team_away['id'],
                'goals_home': goals_home,
                'goals_away': goals_away,
                'year': self.kickoff.year}

    def event_rows(self):
        """
        Get match info at the event-level for csv exporting.
        """
        bg = self._background_info()
        for ftype, e in self.get_timed_events():
            if not utils.is_loc(e):  # skip unlocated events
                continue
            bg['x'] = e.get('start', e.get('loc'))['x']
            bg['y'] = e.get('start', e.get('loc'))['y']
            bg['end_x'] = e.get('end', {'x': ''})['x']
            bg['end_y'] = e.get('end', {'y': ''})['y']
            bg['mins'], bg['secs'] = e['mins'], e['secs']
            bg['ftype'], bg['type'] = ftype, e.get('type', '')
            bg['action_type'] = e.get('action_type', '')
            bg['player_id'] = e['player_id']
            bg['team_id'] = utils.get_team_id(e)
            yield bg

    def xGs(self, **kwargs):
        """
        Get goal attempts info for xG modelling.

        Returns: generator of (bq, seq, feats)
        --------
        bg: dict, background match info (see self._background_info)
        seq: list, sequence of timed and located events leading to the attempt
        feats: dict, extracted features from the attempt
        """
        bg = self._background_info()
        for attempt in self.get_attempts(**kwargs):
            (*attempt, (_, ga)), seq = list(attempt), []
            mins, secs, team_id = ga['mins'], ga['secs'], utils.get_team_id(ga)
            injurytime = ga.get("injurytime_play", None)
            # feats
            feats = {'team_id': ga['team_id'],
                     'player_id': ga['player_id'],
                     'is_home': ga['team_id'] == self.team_home,
                     'headed': ga.get('headed', False),
                     "is_goal": ga['type'] == 'goal',
                     'distance': utils.euclidean(
                         ga['end']['x'], ga['end']['y'], 100, 50),
                     'possession': self.possession(
                         mins, secs, team_id, injurytime=injurytime),
                     'angle': utils.get_angle(ga['end']['x'], ga['end']['y'])}
            # sequential data
            for ftype, e in attempt:
                if not utils.is_loc(e):  # skip unlocated events
                    continue
                seq.append({
                    'x': e.get('start', e.get('loc'))['x'],
                    'y': e.get('start', e.get('loc'))['y'],
                    'end_x': e.get('end', {'x': ''})['x'],
                    'end_y': e.get('end', {'y': ''})['y'],
                    'mins': e['mins'], 'secs': e['secs'],
                    'ftype': ftype, 'type': e.get('type', ''),
                    'action_type': e.get('action_type', ''),
                    'player_id': e['player_id'],
                    'team_id': utils.get_team_id(e)})
            yield bg, seq, feats

    @utils.cache
    def possession(self, mins, secs, team_id, injurytime=None):
        """
        Return ball possession of a given team for the previous 5 minutes
        to a given time (`mins`, `secs`) as a weighted mean of the possession
        in the current and the previous timeslice.
        """
        if injurytime is not None:  # get possession from injury_time keyword
            timeslice = '85 - 90' if mins >= 90 else '40 - 45'
            xpath = POSSESION_IJP.format(timeslice, team_id, "1")
            return int(self.xml.xpath(xpath)[0])
        ts, mins = divmod(mins, 5)
        timeslice = '{} - {}'.format(ts * 5, (ts + 1) * 5)
        if ts * 5 >= 90:        # no injury time, return last timeslice
            return int(self.xml.xpath(POSSESION.format('85 - 90', team_id))[0])
        poss1 = int(self.xml.xpath(POSSESION.format(timeslice, team_id))[0])
        if ts == 0:
            return poss1
        timeslice = '{} - {}'.format((ts - 1) * 5, ts * 5)
        poss0 = int(self.xml.xpath(POSSESION.format(timeslice, team_id))[0])
        weight1 = (mins / 5) + (secs / 60)
        weight0 = ((5 - mins) / 5) + ((60 - secs) / 60)
        return (weight0 * poss0 + weight1 * poss1) / 2

    @utils.cache
    def get_player(self, player_id):
        node = self.xml.xpath(PLAYER.format(player_id))[0]
        return _parse_node(node)

    @utils.cache
    def get_team(self, team_id):
        node = self.xml.xpath(TEAM.format(team_id))[0]
        return _parse_node(node)

    @property
    def filters(self):
        filters = self.xml.xpath('/squawka/data_panel/filters')
        return [c.tag for c in filters[0].getchildren()]

    @property
    def name(self):
        return self.xml.xpath('/squawka/data_panel/game/name/text()')[0]

    @property
    def score(self):
        home_goals = self.xml.xpath(GOAL.format(self.team_home['id']))
        away_goals = self.xml.xpath(GOAL.format(self.team_away['id']))
        return len(home_goals), len(away_goals)

    @property
    def team_home(self):
        team = self.xml.xpath(HOME)[0]
        return self.get_team(team.attrib['id'])

    @property
    def team_away(self):
        team = self.xml.xpath(AWAY)[0]
        return self.get_team(team.attrib['id'])

    @property
    def competition(self):
        match = re.match(COMP_ID, os.path.basename(self.path))
        if match is not None:
            comp, _ = match.groups()
            return comp
        # assume url was given as path
        return re.findall("s3-irl-(.*)\.squawka\.com", self.path)[0]

    @property
    def match_id(self):
        match = re.match(COMP_ID, os.path.basename(self.path))
        if match is not None:
            _, match_id = match.groups()
            return match_id
        # assume url was given as path
        return re.findall("ingame/(.*)", self.path)[0]

    @property
    def kickoff(self):
        date = self.xml.xpath("/squawka/data_panel/game/kickoff/text()")[0]
        return datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')

    @property
    def venue(self):
        return self.xml.xpath("/squawka/data_panel/game/venue/text()")[0]
