
import os
import re
from datetime import datetime
from collections import defaultdict

from lxml import etree

from utils import TIME_SLICE_EVENTS

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

# team_id
TEAM_ID = ('goal_keeping', 'goals_attempts', 'headed_duals', 'interceptions',
           'clearances', 'all_passes')
TEAM = ('tackles', 'crosses', 'corners', 'keepersweeper', 'setpieces',
        'offside')


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


def _get_team_id(ftype, e):
    if 'team_id' in e:
        return e['team_id']
    else:
        return e['team']


def cache(method, prop='_cache'):
    def wrapper(self, arg, *args):
        key = method.__name__
        if not hasattr(self, prop):
            raise ValueError("Class needs a {} property".format(prop))
        cached = getattr(self, prop).get(key, {}).get(arg, None)
        if cached is not None:
            return cached
        item = method(self, arg, *args)
        self._cache[key][arg] = item
        return item
    return wrapper


class SquawkaMatch(object):
    """
    Class wrapping a squawka xml for easy access.
    """
    def __init__(self, path):
        self._cache = defaultdict(lambda: defaultdict(dict))
        self.path = path
        self.xml = self.parse_xml(path)

    @staticmethod
    def parse_xml(f):
        with open(f, 'r') as f:
            return etree.fromstring(bytes(f.read(), 'utf'))

    def __getattr__(self, name):
        if name in TIME_SLICE_EVENTS:
            return self._get_filter_events(name)
        else:
            msg = "'{}' object has no attribute '{}'"
            raise AttributeError(msg.format(type(self).__name__, name))

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
        for f in self.filters:
            try:
                for event in getattr(self, f):
                    if 'mins' in event and 'secs' in event:
                        yield f, event
            except AttributeError:
                continue

    def get_attempts(self):
        events = list(self.get_timed_events())
        events = sorted(events, key=lambda e: (e[1]['mins'], e[1]['secs']))
        for idx, (ftype, e) in enumerate(events):
            if ftype == 'goals_attempts':
                team_id = _get_team_id(ftype, e)
                if idx == 0:
                    yield [(ftype, e)]
                    continue
                attempt, ctx_idx = [], idx - 1
                ctx_ftype, ctx_e = events[ctx_idx]
                while ctx_idx > 0 and _get_team_id(ctx_ftype, ctx_e) == team_id:
                    attempt.append((ctx_ftype, ctx_e))
                    ctx_idx -= 1
                    ctx_ftype, ctx_e = events[ctx_idx]
                yield attempt[::-1] + [(ftype, e)]

    @cache
    def get_player(self, player_id):
        node = self.xml.xpath(PLAYER.format(player_id))
        if len(node) > 0:
            assert len(node) == 1
            return _parse_node(node[0])

    @cache
    def get_team(self, team_id):
        node = self.xml.xpath(TEAM.format(team_id))
        if len(node) > 0:
            assert len(node) == 1
            return _parse_node(node[0])

    @property
    def filters(self):
        filters = self.xml.xpath('/squawka/data_panel/filters')
        if len(filters) != 0:
            return [c.tag for c in filters[0].getchildren()]

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
        comp, _ = re.match(COMP_ID, os.path.basename(self.path)).groups()
        return comp

    @property
    def match_id(self):
        _, match_id = re.match(COMP_ID, os.path.basename(self.path)).groups()
        return match_id

    @property
    def kickoff(self):
        date = self.xml.xpath("/squawka/data_panel/game/kickoff/text()")[0]
        return datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')

    @property
    def venue(self):
        return self.xml.xpath("/squawka/data_panel/game/venue/text()")[0]
