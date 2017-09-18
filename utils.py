
import math


COMPETITIONS = {
    '4': 'World Cup',
    '5': 'Champions League',
    '6': 'Europa League',
    '8': 'English Barclays Premier League',
    '9': 'Dutch Eredivisie',
    '10': 'Football League Championship',
    '21': 'Italian Serie A',
    '22': 'German Bundesliga',
    '23': 'Spanish La Liga',
    '24': 'French Ligue 1',
    '98': 'US Major League Soccer',
    '114': 'Turkish Super Lig',
    '129': 'Russian Premier League',
    '199': 'Mexican Liga MX - Apertura',
    '214': 'Australian A-League',
    '363': 'Brazilian Serie A',
    '385': 'Mexican Liga MX - Clausura',
}


TIME_SLICE_EVENTS = [
    'action_areas',
    'all_passes',
    'balls_out',
    'blocked_events',
    'cards',
    'clearances',
    'corners',
    'crosses',
    'extra_heat_maps',
    'fouls',
    'goal_keeping',
    'goals_attempts',
    'headed_duals',
    'interceptions',
    'keepersweeper',
    'offside',
    'oneonones',
    'setpieces',
    'tackles',
    'takeons',
]


def cache(method, prop='_cache'):
    def wrapper(self, arg, *args, **kwargs):
        key = method.__name__
        if not hasattr(self, prop):
            raise ValueError("Class needs a {} property".format(prop))
        cached = getattr(self, prop).get(key, {}).get(arg, None)
        if cached is not None:
            return cached
        item = method(self, arg, *args, **kwargs)
        self._cache[key][arg] = item
        return item
    return wrapper


def get_team_id(e):
    return e.get('team', e.get('team_id'))


def is_loc(e):
    return ('start' in e and 'end' in e) or 'loc' in e


def transform_loc(x, y):
    """Distances are given in percentages (0-100), here we transform
    into meters by assuming average pitch proportions where length
    is between (90, 100) == 105 meters and width is (45, 90) == 60"""
    return x * 1.05, y * 0.6


def euclidean(x1, y1, x2, y2):
    (x1, y1), (x2, y2) = transform_loc(x1, y1), transform_loc(x2, y2)
    return math.sqrt(((x2 - x1) ** 2) + (abs(y2 - y1) ** 2))


def dotproduct(v1, v2):
    return sum((a*b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dotproduct(v, v))


def angle(v1, v2=None, origin=(100, 50)):
    """Compute angle between two points. Origin defaults to the
    attacking goal. By default the second point is taken to be the corner
    closed to v1 along the y axis"""
    if v2 is None:
        v2 = (100, 0) if v1[1] <= 50 else (100, 100)
    v1 = (v1[0] - origin[0], v1[1] - origin[1])
    v2 = (v2[0] - origin[0], v2[1] - origin[1])
    v1, v2 = transform_loc(*v1), transform_loc(*v2)
    return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))


def to_degrees(radians):
    return radians * (180 / math.pi)
