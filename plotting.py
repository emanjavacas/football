
from collections import defaultdict

from bokeh.plotting import figure
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet, HoverTool

import utils

GREEN = '#60813f'
BLACK = '#130c05'
BROWN = '#5e4206'
ORANGE = '#ffb204'
YELLOW = '#fee300'


def plot_pitch(pw=12, ph=8, plot_height=800, plot_width=1200, title=''):
    fig = figure(
        plot_width=plot_width, plot_height=plot_height,
        x_range=(0, 1), y_range=(0, 1), background_fill_color=GREEN,
        title=title)

    fig.xgrid.grid_line_color, fig.ygrid.grid_line_color = None, None
    fig.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    fig.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    fig.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
    fig.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
    fig.xaxis.major_label_text_font_size = '0pt'  # turn off x-axis tick labels
    fig.yaxis.major_label_text_font_size = '0pt'  # turn off y-axis tick labels

    linesopt = {'color': 'white', 'line_width': 2.5}

    x0, y0 = 0, 0
    x1, y1 = pw * 100, ph * 100
    dx, dy = x1 - x0, y1 - y0
    maxd = max(dx, dy)
    height, width = lambda h: h * maxd / dy, lambda w: w * maxd / dx

    # field
    fig.rect(x=[0.5], y=[0.5], width=1, height=1, fill_alpha=0, **linesopt)
    # left box
    # big box
    fig.line(x=[0/pw, 1.65/pw], y=[2/ph, 2/ph], **linesopt)
    fig.line(x=[0/pw, 1.65/pw], y=[6/ph, 6/ph], **linesopt)
    fig.line(x=[1.65/pw, 1.65/pw], y=[2/ph, 6/ph], **linesopt)
    # small box
    fig.line(x=[0/pw, 0.55/pw], y=[3.1/ph, 3.1/ph], **linesopt)
    fig.line(x=[0/pw, 0.55/pw], y=[4.9/ph, 4.9/ph], **linesopt)
    fig.line(x=[0.55/pw, 0.55/pw], y=[3.1/ph, 4.9/ph], **linesopt)
    # dot
    fig.ellipse(x=[1.1/pw], y=[4/ph],
                width=width(0.007), height=height(0.007),
                **linesopt)

    # right box
    # big box
    fig.line(x=[12/pw, (12-1.65)/pw], y=[2/ph, 2/ph], **linesopt)
    fig.line(x=[12/pw, (12-1.65)/pw], y=[6/ph, 6/ph], **linesopt)
    fig.line(x=[(12-1.65)/pw, (12-1.65)/pw], y=[2/ph, 6/ph], **linesopt)
    # small box
    fig.line(x=[12/pw, (12-0.55)/pw], y=[3.1/ph, 3.1/ph], **linesopt)
    fig.line(x=[12/pw, (12-0.55)/pw], y=[4.9/ph, 4.9/ph], **linesopt)
    fig.line(x=[(12-0.55)/pw, (12-0.55)/pw], y=[3.1/ph, 4.9/ph], **linesopt)
    # dot
    fig.ellipse(x=[(12-1.1)/pw], y=[4/ph],
                width=width(0.007), height=height(0.007),
                **linesopt)

    # middle field
    fig.line(x=[6/pw, 6/pw], y=[0, 1], **linesopt)
    fig.ellipse(x=[6/pw], y=[4/ph],
                width=width(0.3), height=height(0.3),
                fill_alpha=0, **linesopt)
    fig.ellipse(x=[6/pw], y=[4/ph],
                width=width(0.01), height=height(0.01), **linesopt)

    return fig


def _get_team_color(e, match):
    if e.get('team_id', e.get('team')) == match.team_home['id']:
        return BLACK
    else:
        return ORANGE


def _add_forward(fig, ftype, e, match):
    color = _get_team_color(e, match)
    fig.diamond(x=[e['start']['x'] / 100],
                y=[e['start']['y'] / 100],
                size=10, color=color, line_width=2)
    if ftype == 'goals_attempts':
        line_dash = 'dashed'
    else:
        line_dash = 'solid'
    arrow = Arrow(end=NormalHead(fill_color=color, line_color=color),
                  line_color=color, line_width=2, line_dash=line_dash,
                  x_start=e['start']['x'] / 100,
                  y_start=e['start']['y'] / 100,
                  x_end=e['end']['x'] / 100,
                  y_end=e['end']['y'] / 100)
    fig.add_layout(arrow)


def _add_located(fig, ftype, e, match):
    color = _get_team_color(e, match)
    fig.diamond(x=[e['loc']['x'] / 100], y=[e['loc']['y'] / 100],
                color=color, size=10, line_width=2)


def _add_idxs(fig, attempt, match):
    data = defaultdict(list)
    for idx, (ftype, e) in enumerate(attempt):
        data['x'].append(e.get('start', e.get('loc'))['x'] / 100)
        data['y'].append(e.get('start', e.get('loc'))['y'] / 100)
        data['idx'].append(idx)
        data['mins'].append(e['mins'])
        data['secs'].append(e['secs'])
        data['ftype'].append(ftype)
        data['atype'].append(e.get('action_type', ''))
        data['type'].append(e.get('type', ''))
        data['player'].append(match.get_player(e['player_id'])['name'])
        data['team'].append(match.get_team(utils.get_team_id(e))['long_name'])
    source = ColumnDataSource(data=data)
    labels = LabelSet(
        x='x', y='y', text='idx', level='glyph',
        text_color='#d3d3d3', text_font_size='16px', text_font_style='bold',
        x_offset=5, y_offset=-5, source=source, render_mode='css')
    fig.add_layout(labels)
    renderer = fig.circle(x='x', y='y', source=source, size=6)
    hover = HoverTool(
        renderers=[renderer], tooltips=[
            ('index', '@idx'), ('(x,y)', '($x, $y)'),
            ('(mins,secs)', '(@mins, @secs)'), ('ftype', '@ftype'),
            ('atype', '@atype'), ('type', '@type'),
            ('player', '@player'), ('team', '@team')
        ])
    fig.add_tools(hover)


def add_attempt(fig, attempt, match):
    _add_idxs(fig, attempt, match)
    for idx, (ftype, e) in enumerate(attempt):
        if 'start' in e or 'end' in e:
            _add_forward(fig, ftype, e, match)
        elif 'loc' in e:
            _add_located(fig, ftype, e, match)
