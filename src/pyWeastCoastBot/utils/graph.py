import tempfile

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from pyWeastCoastBot.utils.consts import HexColors

# Set backend to Agg for headless environments
plt.switch_backend("Agg")


def generate_line_plot(df, x, y, xlabel=None, ylabel=None, legend_title=None, labels=None):
    """
    Generates a matplotlib figure for a line plot.

    Args:
        df: DataFrame containing the data.
        x: Column name for x-axis or array-like data.
        y: Column name or list of column names for y-axis.
        xlabel: Label for x-axis.
        ylabel: Label for y-axis.
        legend_title: Title for the legend.
        labels: Dict for mapping column names to labels (compatibility with plotly).
    """
    if labels is None:
        labels = {}

    # Resolve labels
    # If x is a string (column name), check labels
    if isinstance(x, str) and x in labels and not xlabel:
        xlabel = labels[x]

    # For y, if it's a single column
    if isinstance(y, str) and y in labels and not ylabel:
        ylabel = labels[y]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Transparent background
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    text_color = HexColors.WHITE

    # Prepare x data
    if isinstance(x, str) and x in df.columns:
        x_data = df[x]
    else:
        x_data = x

    # Try to convert to datetime if it looks like strings/object for better plotting
    try:
        # Check if x_data is pandas Series/Index to access dtype
        if hasattr(x_data, "dtype") and (x_data.dtype == "object" or x_data.dtype == "string"):
            x_data = pd.to_datetime(x_data)
    except Exception:
        # Fallback to original data if conversion fails
        pass

    # Convert to US Eastern timezone if datetime data
    if hasattr(x_data, "dtype") and pd.api.types.is_datetime64_any_dtype(x_data):
        # If timezone-naive, assume UTC then convert
        try:
            if not hasattr(x_data.dtype, "tz") or x_data.dtype.tz is None:
                x_data = pd.DatetimeIndex(x_data).tz_localize("UTC")
            else:
                x_data = pd.DatetimeIndex(x_data)
            x_data = x_data.tz_convert("America/New_York")
        except Exception:
            # If timezone conversion fails, keep original data
            pass

    # Plotting
    if isinstance(y, list):
        for col in y:
            # Get label from labels dict if available, else col name
            label = labels.get(col, col)
            ax.plot(x_data, df[col], label=label, linewidth=3)
    else:
        label = labels.get(y, y)
        ax.plot(x_data, df[y], label=label, linewidth=3)

    # Styling
    for spine in ax.spines.values():
        spine.set_color(text_color)

    ax.tick_params(axis="x", colors=text_color, labelcolor=text_color, labelsize=14)
    ax.tick_params(axis="y", colors=text_color, labelcolor=text_color, labelsize=14)

    if xlabel:
        ax.set_xlabel(xlabel, color=text_color, fontsize=18)
    if ylabel:
        ax.set_ylabel(ylabel, color=text_color, fontsize=18)

    # Legend
    if legend_title or (isinstance(y, list) and len(y) > 1):
        legend = ax.legend(title=legend_title, fontsize=14, title_fontsize=16)
        if legend:
            legend.get_frame().set_alpha(0.0)
            plt.setp(legend.get_texts(), color=text_color)
            if legend.get_title():
                plt.setp(legend.get_title(), color=text_color)

    # Auto-rotate date labels if applicable
    # fig.autofmt_xdate()

    # Use ConciseDateFormatter for better date/time labels
    if hasattr(x_data, "dtype") and pd.api.types.is_datetime64_any_dtype(x_data):
        # Extract timezone from data if available
        tz = None
        if hasattr(x_data, "dtype") and hasattr(x_data.dtype, "tz"):
            tz = x_data.dtype.tz

        locator = mdates.AutoDateLocator(tz=tz)
        formatter = mdates.ConciseDateFormatter(locator, tz=tz)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    plt.tight_layout()
    return fig


def generate_line_plot_image(df, x, y, **kwargs):
    fig = generate_line_plot(df, x, y, **kwargs)
    return write_fig_to_tempfile(fig)


def write_fig_to_tempfile(fig):
    file = tempfile.TemporaryFile()
    fig.savefig(file, format="png", transparent=True, dpi=100)
    plt.close(fig)
    file.seek(0)
    return file
