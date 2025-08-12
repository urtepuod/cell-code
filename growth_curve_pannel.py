import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

def parse_datetime(datetime_str, format_str="%Y-%m-%d %H:%M:%S"):
    return datetime.strptime(datetime_str, format_str)

def calculate_time_differences_in_hours(datetimes, reference_datetime):
    return [(dt - reference_datetime).total_seconds() / 3600.0 for dt in datetimes]

def filter_data_by_hour(time_differences, data, max_hour=50):
    return [(time, value) for time, value in zip(time_differences, data) if time <= max_hour]

def process_control_data_separate_timeline(control_data, max_hour=50):
    if not control_data:
        return []
    control_datetimes = [parse_datetime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in control_data]
    control_values = [val for _, val in control_data]
    control_start = control_datetimes[0]
    control_time_differences = calculate_time_differences_in_hours(control_datetimes, control_start)
    return filter_data_by_hour(control_time_differences, control_values, max_hour=max_hour)

def plot_cell_counts_separate_timelines(
    output_filename,
    sheet_name=None,
    control_data_diluted=None,
    control_data_undiluted=None,
    max_hour=50
):
    # Read excel
    df = pd.read_excel(output_filename, sheet_name=sheet_name)
    df = df.sort_values(by='Folder Name').dropna(subset=['Folder Name', 'Concentration(ml)'])
    dirs = df['Folder Name'].tolist()
    counts = df['Concentration(ml)'].tolist()

    # Main series timeline (from Folder Name: "%y_%m_%d_%H_%M_%S")
    main_datetimes = [datetime.strptime(dt, "%y_%m_%d_%H_%M_%S") for dt in dirs]
    main_start = main_datetimes[0]
    main_hours = calculate_time_differences_in_hours(main_datetimes, main_start)
    main_data = filter_data_by_hour(main_hours, counts, max_hour=max_hour)

    # Controls (separate timelines)
    diluted = process_control_data_separate_timeline(control_data_diluted, max_hour)
    undiluted = process_control_data_separate_timeline(control_data_undiluted, max_hour)
    if diluted:
        diluted = diluted[1:]  # keep your prior skipping

    # Broken y-axis: two stacked panels
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, sharex=True, figsize=(10, 8),
                                         gridspec_kw={"height_ratios": [1, 1]})

    # Axes config
    for ax in (ax_top, ax_bot):
        ax.set_yscale('log')
        ax.tick_params(labelsize=13)
        ax.grid(True, ls='--', alpha=0.3)

    # Labels and y-limits
    ax_bot.set_xlabel("Time (hours since dataset start)", fontsize=16)
    ax_top.set_ylabel("Cell Concentration (CFU/ml)", fontsize=16, color='tab:blue')
    ax_bot.set_ylabel("Cell Concentration (CFU/ml)", fontsize=16, color='tab:blue')
    ax_bot.set_ylim(1e6, 1e9)       # zoom range
    ax_top.set_ylim(5e11, 7e11)     # high range (top shows ~7×10^11)

    # Plot main data on both panels
    if main_data:
        t_main, v_main = zip(*main_data)
        for ax in (ax_top, ax_bot):
            ax.plot(t_main, v_main, marker='o', color='tab:blue', label='Device')
        ax_bot.set_xlim(0, t_main[-1])
    else:
        print("No main data to plot after filtering.")

    # Theoretical minimum line (bottom panel)
    ax_bot.axhline(1.74e6, color='gray', linestyle='--')

    # Controls on bottom panel
    if diluted:
        t_d, v_d = zip(*diluted)
        ax_bot.plot(t_d, v_d, marker='o', color='tab:red', label='Diluted')
    if undiluted:
        t_u, v_u = zip(*undiluted)
        ax_bot.plot(t_u, v_u, marker='s', color='tab:red', label='Undiluted')

    # Legend (bottom only)
    handles, labels = ax_bot.get_legend_handles_labels()
    if handles:
        ax_bot.legend(handles, labels, loc='upper left', fontsize=12)

    # Title (match your style)
    ax_bot.set_title('AD38 Cell Concentration vs Time', fontsize=20)

    # Visual break marks between panels
    ax_top.spines.bottom.set_visible(False)
    ax_bot.spines.top.set_visible(False)
    ax_top.tick_params(labeltop=False)
    ax_bot.xaxis.tick_bottom()
    d = .015
    kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False, lw=2)
    ax_top.plot((-d, +d), (-d, +d), **kwargs)
    ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    kwargs.update(transform=ax_bot.transAxes)
    ax_bot.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax_bot.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

    fig.tight_layout()
    return fig

# --- Example static inputs -------------------------------------------------------
OUTPUT_FILE = Path(r'C:\Users\s1741477\Desktop\data\ad38\11_18_24\cell_counts_summary.xlsx')
SHEET_NAME = "Sheet1"

CONTROL_DILUTED = [
    ("2024-03-01 18:40:00", 3.09e6), ("2024-03-02 10:07:00", 1.81e8),
    ("2024-03-02 13:07:00", 2.78e8), ("2024-03-02 16:51:00", 3.97e8),
    ("2024-03-02 18:17:00", 4.90e8), ("2024-03-03 13:40:00", 8.33e8),
    ("2024-03-03 16:05:00", 5.78e8), ("2024-03-03 17:37:00", 5.38e8),
]
CONTROL_UNDILUTED = [
    ("2024-03-01 17:29:00", 1.75e8), ("2024-03-02 10:02:00", 2.86e8),
    ("2024-03-02 13:40:00", 6.70e8), ("2024-03-02 17:15:00", 1.72e9),
    ("2024-03-02 18:15:00", 2.11e9), ("2024-03-03 12:57:00", 5.98e9),
    ("2024-03-03 16:10:00", 1.27e11), ("2024-03-03 18:20:00", 1.27e11),
]

# --- Panel Dashboard -------------------------------------------------------------
import panel as pn
from io import BytesIO
pn.extension()  # don't pass 'matplotlib'

# Widgets
x_max_hours = pn.widgets.IntSlider(name="X-axis max (h)", start=1, end=100, value=50)
format_select = pn.widgets.Select(name="Format", options=["png", "tiff"], value="png")
filename_input = pn.widgets.TextInput(name="Filename", value="cell_plot")
show_diluted = pn.widgets.Checkbox(name="Show diluted", value=True)
show_undiluted = pn.widgets.Checkbox(name="Show undiluted", value=True)

# Download: provide a file-like object
def generate_file():
    buf = BytesIO()
    fig = plot_cell_counts_separate_timelines(
        output_filename=OUTPUT_FILE,
        sheet_name=SHEET_NAME,
        control_data_diluted=CONTROL_DILUTED if show_diluted.value else None,
        control_data_undiluted=CONTROL_UNDILUTED if show_undiluted.value else None,
        max_hour=x_max_hours.value
    )
    fig.savefig(buf, format=format_select.value, dpi=300, bbox_inches="tight")
    buf.seek(0)
    return buf

download_button = pn.widgets.FileDownload(
    file=generate_file,
    filename=f"{filename_input.value}.{format_select.value}",
    embed=False
)

# Update filename dynamically
def _update_filename(event):
    download_button.filename = f"{filename_input.value}.{format_select.value}"
filename_input.param.watch(_update_filename, 'value')
format_select.param.watch(_update_filename, 'value')

# Reactive plot pane
@pn.depends(x_max_hours, show_diluted, show_undiluted)
def live_plot(x_max_hours, show_diluted, show_undiluted):
    fig = plot_cell_counts_separate_timelines(
        output_filename=OUTPUT_FILE,
        sheet_name=SHEET_NAME,
        control_data_diluted=CONTROL_DILUTED if show_diluted else None,
        control_data_undiluted=CONTROL_UNDILUTED if show_undiluted else None,
        max_hour=x_max_hours
    )
    return pn.pane.Matplotlib(fig, tight=True)

controls = pn.Column(
    "## Controls",
    x_max_hours, show_diluted, show_undiluted,
    pn.Spacer(height=15),
    "## Download",
    filename_input, format_select, download_button,
    width=300
)

dashboard = pn.Row(
    controls,
    live_plot,
    sizing_mode="stretch_both"
)

# Serve when run directly
if __name__ == "__main__":
    pn.serve(dashboard, title="Cell-count Plotter", show=True, autoreload=True)