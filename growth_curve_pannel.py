import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

def parse_datetime(datetime_str, format_str="%Y-%m-%d %H:%M:%S"):
    """Parse a datetime string into a datetime object."""
    return datetime.strptime(datetime_str, format_str)

def calculate_time_differences_in_hours(datetimes, reference_datetime):
    """Calculate the time differences in hours relative to the given reference datetime."""
    return [(dt - reference_datetime).total_seconds() / 3600.0 for dt in datetimes]

def filter_data_by_hour(time_differences, data, max_hour=50):
    """Filter data points to include only up to a specified hour."""
    return [(time, value) for time, value in zip(time_differences, data) if time <= max_hour]

def process_control_data_separate_timeline(control_data, max_hour=50):
    """
    Process a control dataset (undiluted or diluted) with its own timeline.
    Returns filtered (time, value) pairs or an empty list if no data.
    """
    if not control_data:
        return []

    control_datetimes = [parse_datetime(ts, "%Y-%m-%d %H:%M:%S") for ts, _ in control_data]
    control_values = [val for _, val in control_data]
    control_start = control_datetimes[0]
    control_time_differences = calculate_time_differences_in_hours(control_datetimes, control_start)
    return filter_data_by_hour(control_time_differences, control_values, max_hour=max_hour)

def plot_cell_counts_separate_timelines(output_filename, 
                                        save_path=None, 
                                        sheet_name=None, 
                                        control_data_diluted=None, 
                                        control_data_undiluted=None,
                                        std_devs=None,
                                        max_hour=50):
    """
    Plot the main dataset along with undiluted and diluted control datasets,
    each having their own timeline starting at zero. Also adds a short y-axis
    extension (dashed) and a dashed horizontal dash with a 'Theoretical max: 6.4×10¹¹' label—
    raised above the title. Then marks the theoretical minimum with a short dash
    starting exactly at the y-axis (x=0) and a text label (no arrow).
    """
    # Read the Excel file
    df = pd.read_excel(output_filename, sheet_name=sheet_name)
    df = df.sort_values(by='Folder Name').dropna(subset=['Folder Name', 'Concentration(ml)'])
    dirs = df['Folder Name'].tolist()
    counts = df['Concentration(ml)'].tolist()

    # Parse main datetimes (format "%y_%m_%d_%H_%M_%S")
    main_datetimes = [datetime.strptime(dt, "%y_%m_%d_%H_%M_%S") for dt in dirs]
    main_start = main_datetimes[0]
    main_hours = calculate_time_differences_in_hours(main_datetimes, main_start)
    main_data = filter_data_by_hour(main_hours, counts, max_hour=max_hour)

    # Process controls
    diluted = process_control_data_separate_timeline(control_data_diluted, max_hour)
    undiluted = process_control_data_separate_timeline(control_data_undiluted, max_hour)

    # Optionally skip the first diluted point
    diluted = diluted[1:] if len(diluted) > 1 else diluted

    # Begin plotting (BROKEN Y-AXIS: top/bottom panels; bottom is 'ax1' to keep rest unchanged)
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [1, 1]})
    ax1 = ax_bot  # keep existing code that uses ax1

    # Your original axis setup (applies to bottom panel)
    ax1.set_xlabel("Time (hours since each dataset's start)", fontsize=16)
    ax1.set_ylabel("Cell Concentration (CFU/ml)", color='tab:blue', fontsize=16)
    ax1.set_yscale('log')
    ax1.set_ylim(1e6, 1e9)  # Visible range up to 1e9

    # Also configure the top panel to show the high range (broken axis)
    ax_top.set_yscale('log')
    ax_top.set_ylabel("Cell Concentration (CFU/ml)", fontsize=16, color='tab:blue')
    ax_top.set_ylim(5e11, 7e11)  # top axis range (shows up to ~7×10^11)

    # Make both panels consistent for ticks/grid
    for ax in (ax_top, ax_bot):
        ax.tick_params(labelsize=13)
        ax.grid(True, ls='--', alpha=0.3)

    # --------------------------------------------------
    # 1) Draw a dashed vertical extension of the y-axis above 1e9 (on bottom panel)
    # --------------------------------------------------
    y_ext = 1.10
    ax1.plot(
        [0.0, 0.0],      # x in axes-fraction (exactly on y-axis spine)
        [1.0, y_ext],    # y in axes-fraction (from top of axis to above title)
        transform=ax1.transAxes,
        color="black",
        linestyle="--",
        linewidth=1.5,
        clip_on=False
    )

    # --------------------------------------------------
    # 2) Draw a dashed horizontal dash at y_ext to mark the theoretical max
    # --------------------------------------------------
    dash_len = 0.02  # half-width of dash in axes-fraction
    ax1.plot(
        [-dash_len, dash_len],
        [y_ext,       y_ext],
        transform=ax1.transAxes,
        color="black",
        linestyle="--",
        linewidth=1.5,
        clip_on=False
    )

    # --------------------------------------------------
    # 3) Label that dash: 'Theoretical max: 6.4×10¹¹'
    # --------------------------------------------------
    text_offset = 0.005
    ax1.text(
        dash_len + text_offset,
        y_ext,
        "Theoretical max: 6.4×10¹¹",
        transform=ax1.transAxes,
        ha="left",
        va="center",
        fontsize=12,
        color="black"
    )

    # --------------------------------------------------
    # 4) Plot the main dataset (bottom panel)
    # --------------------------------------------------
    if main_data:
        times_main, vals_main = zip(*main_data)
        ax1.plot(times_main, vals_main,
                 marker='o', color='tab:blue', label='Cell Concentration (Device)')
        # Ensure x-axis starts exactly at 0
        x_max = times_main[-1]
        ax1.set_xlim(0, x_max)

        # If you want the star (as in your original) on bottom panel:
        ax1.plot(0, 1e7, marker='*', color='green', markersize=12)
    else:
        print("No main data to plot after filtering.")

    ax1.tick_params(axis='both', which='major', labelsize=13)

    # --------------------------------------------------
    # 5) Mark the theoretical minimum on bottom panel
    # --------------------------------------------------
    if main_data:
        x_max = times_main[-1]
        dash_len_data = 0.05 * x_max  # extend ~5% of the x-range

        ax1.plot(
            [0, dash_len_data],
            [1.74e6, 1.74e6],
            color='gray',
            linestyle='--',
            linewidth=1
        )

        text_offset_data = 0.02 * x_max
        ax1.text(
            dash_len_data + text_offset_data,
            1.74e6,
            "Theoretical min: 1.74×10⁶",
            ha="left",
            va="center",
            fontsize=12,
            color="gray"
        )
    else:
        print("No main data to mark theoretical minimum.")

    # --------------------------------------------------
    # 6) Plot controls on secondary axis (bottom panel twin y)
    # --------------------------------------------------
    if diluted or undiluted:
        ax2 = ax1.twinx()
        ax2.set_ylabel("Control Cell Concentration (CFU/ml)", color='tab:red', fontsize=16)
        ax2.set_yscale('log')
        ax2.set_ylim(1e6, 1e9)
        ax2.tick_params(axis='y', which='major', labelsize=14)

        # Diluted control (with optional error bars)
        if diluted:
            times_dil, vals_dil = zip(*diluted)
            if std_devs and len(std_devs) == len(diluted):
                ax2.errorbar(times_dil, vals_dil, yerr=std_devs,
                             fmt='^', color='tab:red', capsize=5,
                             label='Diluted Control')
            else:
                ax2.plot(times_dil, vals_dil,
                         marker='o', color='tab:red', label='Control (OD)')

        # Undiluted control
        if undiluted:
            times_undil, vals_undil = zip(*undiluted)
            ax2.plot(times_undil, vals_undil,
                     marker='s', color='tab:red', label='Control (OD)')

    # Combine legends on bottom panel
    lines, labels = ax1.get_legend_handles_labels()
    if diluted or undiluted:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=14)
    else:
        ax1.legend(lines, labels, loc='upper left')

    plt.title('AD38 (deltaMotAB MG1655) Cell Concentration vs Time', fontsize=21)

    # Visual break between panels
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

    if save_path:
        plt.savefig(save_path, format='tiff', dpi=300)
        print(f"Plot saved as TIFF at: {save_path}")

    plt.show()


# Example usage (adjust paths and uncomment controls/std_devs as needed):
output_filename = r'C:\Users\s1741477\Desktop\data\ad38\11_18_24\cell_counts_summary.xlsx'
# Note: missing backslash fixed below
save_path = r'C:\Users\s1741477\Desktop\data\ad38\11_18_24\ad38_counts_separate_timeline_controls.tiff'
sheet_name = 'Sheet1'
std_devs = [3.77E+07, 5.89E+07, 3.35E+08, 7.36E+08, 1.25E+09, 1.42E+09, 7.72E+08, 2.27E+09]

control_data_diluted = [
    ('2024-03-01 18:40:00', 3.09*10**6),
    ('2024-03-02 10:07:00', 1.81*10**8),
    ('2024-03-02 13:07:00', 2.78*10**8),
    ('2024-03-02 16:51:00', 3.97*10**8),
    ('2024-03-02 18:17:00', 4.90*10**8),    
    ('2024-03-03 13:40:00', 8.33*10**8),
    ('2024-03-03 16:05:00', 5.78*10**8),
    ('2024-03-03 17:37:00', 5.38*10**8)
]
control_data_undiluted = [
    ('2024-03-01 17:29:00', 1.75e8),
    ('2024-03-02 10:02:00', 2.86e8),
    ('2024-03-02 13:40:00', 6.70e8),
    ('2024-03-02 17:15:00', 1.72e9),
    ('2024-03-02 18:15:00', 2.11e9),
    ('2024-03-03 12:57:00', 5.98e9),
    ('2024-03-03 16:10:00', 1.27e11),
    ('2024-03-03 18:20:00', 1.27e11),
]

plot_cell_counts_separate_timelines(
    output_filename,
    save_path=save_path,
    sheet_name=sheet_name,
    control_data_diluted=control_data_diluted,
    # control_data_undiluted=control_data_undiluted,
    # std_devs=std_devs,
    max_hour=50
)


'''
1:200 dilution

OD values for mg1655
15:43: 0.016
18:03 0.024
23:26 0.169
05:10 0.639
06:21 0.721
10:15 1.15
12:38 1.16
15:05 1.34
10:07 1.78

OD values for ad38
11:39:0.023
12:23 0.024
15:31 0.034
19:33 0.116
21:13 0.214
00:01 0.442
02:18 0.624
07:49 0.980
13:28 1.13
23:23 1.23
'''