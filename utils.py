

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


def get_team_id(e):
    return e.get('team', e.get('team_id'))


def is_loc(e):
    return ('start' in e and 'end' in e) or 'loc' in e
