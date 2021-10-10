import tempfile

import plotly.express as px
from lib.utils.consts import HexColors


def generate_line_plot_image(*args, **kwargs):
    fig = px.line(*args, **kwargs)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=HexColors.WHITE, size=16),
    )
    fig.update_traces(line=dict(width=3))
    return write_fig_to_tempfile(fig)


def write_fig_to_tempfile(fig):
    img_bytes = fig.to_image(format="png", scale=2)
    file = tempfile.TemporaryFile()
    file.write(img_bytes)
    file.seek(0)
    return file
