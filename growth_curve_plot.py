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

    # Begin plotting
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [1, 1]})
    ax1 = ax_bot  # keep the rest of your code unchanged (it uses ax1)
    for ax in (ax_top, ax_bot):
        ax.set_yscale('log')
        ax.tick_params(labelsize=13)
        ax.grid(True, ls='--', alpha=0.3)

    ax_top.set_ylabel("Cell Concentration (CFU/ml)", fontsize=16, color='tab:blue')
    ax_bot.set_ylabel("Cell Concentration (CFU/ml)", fontsize=16, color='tab:blue')

    ax_bot.set_ylim(1e6, 1e9)      # bottom zoom range
    ax_top.set_ylim(5e11, 7e11)    # top high range (~7×10^11)
        
    # --------------------------------------------------
    # 1) Draw a dashed vertical extension of the y-axis above 1e9
    # --------------------------------------------------
    # Also draw main series on the top (broken) axis
    ax_top.plot(times_main, vals_main, marker='o', color='tab:blue', label='Device')

    # If you want the green star on top too:
    ax_top.plot(0, 1e7, marker='*', color='green', markersize=12)
        # In axes-fraction: y=1.00 is the top of plotting area; extend to y_ext=1.10 to go above the title
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

    


    # --------------------------------------------------
    # 4) Plot the main dataset
    # --------------------------------------------------

    if main_data:
        times_main, vals_main = zip(*main_data)
        ax1.plot(times_main, vals_main,
                 marker='o', color='tab:blue', label='Cell Concentration (Device)')
        # Ensure x-axis starts exactly at 0
        x_max = times_main[-1]
        ax1.set_xlim(0, x_max)
    else:
        print("No main data to plot after filtering.")

    ax1.tick_params(axis='both', which='major', labelsize=13)

    # --------------------------------------------------
    # 5) Mark the theoretical minimum with a short dash starting at x=0 (y-axis) and a label
    # --------------------------------------------------

    if main_data:
        x_max = times_main[-1]
        # length of the dash in data-units (e.g., 5% of x_max)
        dash_len_data = 0.05 * x_max  # start at 0, extend 5% of the max hour

        # Draw a short horizontal dashed segment at y=1.74e6 from x=0 to x=dash_len_data
        ax1.plot(
            [0, dash_len_data],  # start at y-axis (x=0), extend right
            [1.74e6, 1.74e6],    # constant y = 1.74e6
            color='gray',
            linestyle='--',
            linewidth=1
        )

        # Place text label just to the right of the dash
        text_offset_data = 0.02 * x_max  # shift text a bit further to the right
        ax1.text(
            dash_len_data + text_offset_data,  # data coordinate
            1.74e6,                            # data y-value
            "Theoretical min: 1.74×10⁶",
            ha="left",
            va="center",
            fontsize=12,
            color="gray"
        )
    else:
        print("No main data to mark theoretical minimum.")

    # --------------------------------------------------
    # 6) Plot controls on secondary axis (if provided)
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

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    if diluted or undiluted:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=14)
    else:
        ax1.legend(lines, labels, loc='upper left')

    plt.title('AD38 (deltaMotAB MG1655) Cell Concentration vs Time', fontsize=21)
    fig.tight_layout()

    if save_path:
        plt.savefig(save_path, format='tiff', dpi=300)
        print(f"Plot saved as TIFF at: {save_path}")

    plt.show()


# Example usage (adjust paths and uncomment controls/std_devs as needed):
output_filename = r'C:\Users\s1741477\Desktop\data\ad38\11_18_24\cell_counts_summary.xlsx'
save_path = r'C:\Users\s1741477\Desktop\data\ad38\11_18_24ad38_counts_separate_timeline_controls.tiff'
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

AD38
    ('2024-03-01 11:39:00', 1.83*10**7),
    ('2024-03-01 12:23:00', 1.84*10**7),
    ('2024-03-01 15:31:00', 1.90*10**7),
    ('2024-03-01 19:33:00', 2.51*10**7),
    ('2024-03-01 21:13:00', 3.50*10**7),    
    ('2024-03-02 00:01:00', 7.57*10**7),
    ('2024-03-02 02:18:00', 1.41*10**8),
    ('2024-03-02 07:49:00', 4.72*10**8),
    ('2024-03-02 13:28:00', 7.85*10**8),
    ('2024-03-02 23:23:00', 1.23*10**9)

MG1655
    ('2024-03-01 15:43:00', 3.25*10**6),
    ('2024-03-01 18:03:00', 3.40*10**6),
    ('2024-03-01 23:26:00', 7.67*10**6),
    ('2024-03-02 05:10:00', 1.07*10**8),
    ('2024-03-02 06:21:00', 1.69*10**8),    
    ('2024-03-02 10:15:00', 1.88*10**9),
    ('2024-03-02 12:38:00', 1.98*10**9),
    ('2024-03-02 15:05:00', 5.44*10**9),
    ('2024-03-03 10:07:00', 6.42*10**10),
]

AD38 01/18/24 diluted od 1.0
    ('2024-03-01 18:40:00', 1.40*10**8),
    ('2024-03-02 10:07:00', 6.60*10**8),
    ('2024-03-02 13:07:00', 1.10*10**10),
    ('2024-03-02 16:51:00', 2.20*10**9),
    ('2024-03-02 18:17:00', 2.16*10**10),    
    ('2024-03-03 13:40:00', 1.37*10**11),
    ('2024-03-03 16:05:00', 1.58*10**10),
    ('2024-03-03 17:37:00', 2.88*10**10)


AD28 18/11/24 diluted od 3.0
    ('2024-03-01 17:29:00', 2.70*10**6),
    ('2024-03-02 10:02:00', 4.62*10**7),
    ('2024-03-02 13:40:00', 1.22*10**8),
    ('2024-03-02 17:15:00', 2.05*10**8),
    ('2024-03-02 18:15:00', 2.23*10**8),    
    ('2024-03-03 12:57:00', 3.15*10**8),
    ('2024-03-03 16:10:00', 5.85*10**8),
    ('2024-03-03 18:20:00', 5.58*10**8)

AD28 18/11/24 undiluted od 3.0
    ('2024-03-01 17:29:00', 1.75*10**7),
    ('2024-03-02 10:02:00', 2.86*10**7),
    ('2024-03-02 13:40:00', 6.70*10**7),
    ('2024-03-02 17:15:00', 1.72*10**8),
    ('2024-03-02 18:15:00', 2.11*10**8),    
    ('2024-03-03 12:57:00', 5.98*10**8),
    ('2024-03-03 16:10:00', 1.27*10**10),
    ('2024-03-03 18:20:00', 1.27*10**10)

AD38 24/11/24 diluted od 1.76
    
    ('2024-11-18 18:22:00', 1.74*10**7),
    ('2024-11-19 11:20:00', 1.04*10**8),
    ('2024-11-19 13:56:00', 2.24*10**8),
    ('2024-11-19 15:45:00', 2.94*10**8),
    ('2024-11-19 16:50:00', 3.33*10**8),
    ('2024-11-19 17:50:00', 3.70*10**8),
    ('2024-11-19 18:54:00', 3.99*10**8),
    ('2024-11-20 12:43:00', 8.99*10**8),
    ('2024-11-20 16:09:00', 9.62*10**8),
    ('2024-11-20 18:10:00', 9.62*10**8)

 AD38 24/11/24 undiluted od 1.76
    ('2024-11-18 18:22:00', 1.74*10**7),
    ('2024-11-19 11:20:00', 1.04*10**8),
    ('2024-11-19 13:56:00', 2.24*10**8),
    ('2024-11-19 15:45:00', 2.94*10**8),
    ('2024-11-19 16:50:00', 3.33*10**8),
    ('2024-11-19 17:50:00', 3.70*10**8),
    ('2024-11-19 18:54:00', 3.99*10**8),
    ('2024-11-20 12:42:00', 8.77*10**8),
    ('2024-11-20 16:08:00', 1.04*10**9),
    ('2024-11-20 18:10:00', 1.04*10**9)

AD38 26/11/24 2mg/ml starch  
    ('2024-11-18 18:22:00', 1.74*10**7),
    ('2024-11-19 11:20:00', 1.04*10**8),
    ('2024-11-19 13:56:00', 2.24*10**8),
    ('2024-11-19 15:45:00', 2.94*10**8),
    ('2024-11-19 16:50:00', 3.33*10**8),
    ('2024-11-19 17:50:00', 3.70*10**8),
    ('2024-11-19 18:54:00', 3.99*10**8),
    ('2024-11-20 12:42:00', 8.77*10**8),
    ('2024-11-20 16:08:00', 1.04*10**9),
    ('2024-11-20 18:10:00', 1.04*10**9)

AD38 09/12/24 5mg/ml starch  
    ('2024-11-18 17:10:00', 3.96*10**7),
    ('2024-11-19 10:50:00', 1.59*10**8),
    ('2024-11-19 13:50:00', 3.16*10**8),
    ('2024-11-19 16:50:00', 5.62*10**8),
    ('2024-11-20 16:50:00', 7.79*10**8),
    ('2024-11-20 17:50:00', 1.48*10**9),
    ('2024-11-21 18:54:00', 7.66*10**8)


AD38 30_01_25 2mg/ml starch  
    ('2024-11-18 19:32:00', 3.96*10**7),
    ('2024-11-19 10:13:00', 1.59*10**8),
    ('2024-11-19 12:40:00', 3.16*10**8),
    ('2024-11-19 16:43:00', 5.62*10**8),
    ('2024-11-19 18:00:00', 7.79*10**8),
    ('2024-11-20 15:00:00', 1.48*10**9),
    ('2024-11-20 18:00:00', 7.66*10**8)

 AD38 25/01/25 diluted   
    ('2024-03-01 18:40:00', 2.10*10**6),
    ('2024-03-02 10:07:00', 1.23*10**8),
    ('2024-03-02 13:07:00', 1.89*10**8),
    ('2024-03-02 16:51:00', 2.70*10**8),
    ('2024-03-02 18:17:00', 3.33*10**8),    
    ('2024-03-03 13:40:00', 5.67*10**8),
    ('2024-03-03 16:05:00', 3.93*10**8),
    ('2024-03-03 17:37:00', 3.66*10**8)
'''
