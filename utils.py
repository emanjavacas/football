
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

from bokeh.plotting import figure
from bokeh.models import Arrow, NormalHead, ColumnDataSource, LabelSet


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


def plot_pitch_plt(pw=12, ph=8):
    fig = plt.figure(figsize=(pw, ph))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor('green')
    ax.set_xticks([])
    ax.set_yticks([])

    lineopts = {'lw': 2.5, 'color': 'white', 'ls': '-'}

    x0, y0 = ax.transAxes.transform((0, 0))  # lower left in pixels
    x1, y1 = ax.transAxes.transform((1, 1))  # upper right in pixes
    dx, dy = x1 - x0, y1 - y0
    maxd = max(dx, dy)
    height, width = lambda h: h * maxd / dy, lambda w: w * maxd / dx

    # left box
    # big box
    ax.add_line(plt.Line2D((0/pw, 1.65/pw), (2/ph, 2/ph), **lineopts))
    ax.add_line(plt.Line2D((0/pw, 1.65/pw), (6/ph, 6/ph), **lineopts))
    ax.add_line(plt.Line2D((1.65/pw, 1.65/pw), (2/ph, 6/ph), **lineopts))
    # small box
    ax.add_line(plt.Line2D((0/pw, 0.55/pw), (3.1/ph, 3.1/ph), **lineopts))
    ax.add_line(plt.Line2D((0/pw, 0.55/pw), (4.9/ph, 4.9/ph), **lineopts))
    ax.add_line(plt.Line2D((0.55/pw, 0.55/pw), (3.1/ph, 4.9/ph), **lineopts))
    # dot
    dot = Ellipse(
        (1.1/pw, 4/ph), width=width(0.007), height=height(0.007), fc='w')
    ax.add_patch(dot)

    # right box
    # big box
    ax.add_line(plt.Line2D((12/pw, (12-1.65)/pw), (2/ph, 2/ph), **lineopts))
    ax.add_line(plt.Line2D((12/pw, (12-1.65)/pw), (6/ph, 6/ph), **lineopts))
    ax.add_line(plt.Line2D(((12-1.65)/pw, (12-1.65)/pw), (2/ph, 6/ph),
                           **lineopts))
    # small box
    l1 = plt.Line2D((12/pw, (12-0.55)/pw), (3.1/ph, 3.1/ph), **lineopts)
    ax.add_line(l1)
    l2 = plt.Line2D((12/pw, (12-0.55)/pw), (4.9/ph, 4.9/ph), **lineopts)
    ax.add_line(l2)
    l3 = plt.Line2D(((12-0.55)/pw, (12-0.55)/pw), (3.1/ph, 4.9/ph), **lineopts)
    ax.add_line(l3)
    # dot
    dot = Ellipse(
        ((12-1.1)/pw, 4/ph), width=width(0.007), height=height(0.007), fc='w')
    ax.add_patch(dot)

    # middle field
    ax.add_line(plt.Line2D((6/pw, 6/pw), (0, 1), **lineopts))
    circle = Ellipse(
        (6/pw, 4/ph),
        width=width(0.3), height=height(0.3),
        ec='w', fc='none', lw=2.5)
    ax.add_patch(circle)
    dot = Ellipse((6/pw, 4/ph), width=width(0.01), height=height(0.01), fc='w')
    ax.add_patch(dot)

    return fig


def plot_pitch(pw=12, ph=8, plot_height=800, plot_width=1200, title=''):
    fig = figure(
        plot_width=plot_width, plot_height=plot_height,
        x_range=(0, 1), y_range=(0, 1), background_fill_color='green',
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


def add_attempt(fig, attempt):
    for idx, (ftype, e) in enumerate(attempt):
        fig.diamond(x=[e['start']['x'] / 100],
                    y=[e['start']['y'] / 100],
                    size=10, color="black", line_width=2)
        arrow_from = 'start'
        if 'middle' in e:
            fig.line(x=[e['start']['x']/100, e['middle']['x']/100],
                     y=[e['start']['y']/100, e['middle']['y']/100],
                     color='black')
            arrow_from = 'middle'
        arrow = Arrow(end=NormalHead(fill_color='black'),
                      x_start=e[arrow_from]['x'] / 100,
                      y_start=e[arrow_from]['y'] / 100,
                      x_end=e['end']['x'] / 100,
                      y_end=e['end']['y'] / 100)
        fig.add_layout(arrow)

    source = ColumnDataSource(data={
        'x': [e['start']['x']/100 for _, e in attempt],
        'y': [e['start']['y']/100 for _, e in attempt],
        'idx': [idx for idx in range(len(attempt))]
    })
    labels = LabelSet(
        x='x', y='y', text='idx', level='glyph',
        x_offset=5, y_offset=-5, source=source, render_mode='canvas')

    fig.add_layout(labels)
