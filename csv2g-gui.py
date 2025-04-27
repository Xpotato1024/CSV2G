import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

def analyze_file(file_path, params):
    try:
        df = pd.read_csv(file_path, skiprows=[int(x.strip()) for x in params['skip_rows'].split(',')])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV: {e}")
        return

    time = pd.to_datetime(df[params['time_col']])
    time_seconds = (time - time.iloc[0]).dt.total_seconds()
    voltage = df[params['voltage_col']].astype(float)

    # 移動平均処理
    voltage_smoothed = voltage.rolling(window=int(params['moving_avg']), center=True, min_periods=1).mean()

    # ベースライン検出
    origin_time = detect_origin_time(voltage_smoothed, time_seconds, params['baseline_tol'])

    time_shifted = time_seconds - origin_time
    voltage_shifted = voltage

    # ステップ応答判別
    is_step_response = detect_step_response(time_shifted, voltage_smoothed, params['settle_time'], params['settle_tol'], params['peak_tol'])

    # グラフ描画
    save_dir = os.path.join(os.path.dirname(__file__), 'dump')  # /dump/に保存
    os.makedirs(save_dir, exist_ok=True)
    plot_and_save_graph(time_shifted, voltage_shifted, save_dir, file_path, params['plot_range_min'], params['plot_range_max'])

    # グラフとステップ応答判別結果を表示
    output_path = os.path.join(save_dir, os.path.splitext(os.path.basename(file_path))[0] + '_dump.png')
    show_graph(output_path, is_step_response, file_path)

def detect_origin_time(voltage_smoothed, time_seconds, baseline_tol):
    baseline_voltage = voltage_smoothed.iloc[0]
    origin_index = None
    for i in range(1, len(voltage_smoothed)):
        if abs(voltage_smoothed.iloc[i] - baseline_voltage) > baseline_tol:
            origin_index = i
            break
    return time_seconds.iloc[origin_index] if origin_index is not None else time_seconds.iloc[0]

def detect_step_response(time_shifted, voltage_smoothed, settle_time, settle_tolerance, peak_tolerance):
    positive_time_mask = time_shifted >= 0
    time_pos = time_shifted[positive_time_mask]
    voltage_pos = voltage_smoothed[positive_time_mask]

    if len(voltage_pos) == 0:
        return False

    initial_voltage = voltage_pos.iloc[0]
    peak_voltage = np.max(voltage_pos)
    bottom_voltage = np.min(voltage_pos)
    peak_variation = max(abs(peak_voltage - initial_voltage), abs(bottom_voltage - initial_voltage))

    if peak_variation < peak_tolerance:
        return False

    settle_mask = (time_pos >= settle_time)
    voltage_settled = voltage_pos[settle_mask]

    if len(voltage_settled) == 0:
        return False

    std_settled = voltage_settled.std()

    return std_settled < settle_tolerance

def plot_and_save_graph(time_shifted, voltage_shifted, save_dir, file_path, plot_range_min, plot_range_max):
    mask = (time_shifted >= plot_range_min) & (time_shifted <= plot_range_max)
    plt.figure(figsize=(10, 5))
    plt.plot(time_shifted[mask], voltage_shifted[mask], label='Voltage')
    plt.xlabel('Time [s]')
    plt.ylabel('Voltage [V]')
    plt.title('V-t Graph (Zeroed)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(save_dir, os.path.splitext(os.path.basename(file_path))[0] + '_dump.png')
    plt.savefig(output_path, dpi=300)
    plt.close()

def select_file_and_analyze(entries):
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return

    params = {
        'time_col': entries['TIME_COL'].get(),
        'voltage_col': entries['VOLTAGE_COL'].get(),
        'skip_rows': entries['SKIP_ROWS'].get(),
        'moving_avg': int(entries['MOVING_AVERAGE_WINDOW'].get()),
        'baseline_tol': float(entries['VOLTAGE_TOLERANCE'].get()),
        'plot_range_min': float(entries['PLOT_RANGE_MIN'].get()),
        'plot_range_max': float(entries['PLOT_RANGE_MAX'].get()),
        'settle_time': float(entries['SETTLE_TIME'].get()),
        'settle_tol': float(entries['SETTLE_TOLERANCE'].get()),
        'peak_tol': float(entries['PEAK_TOLERANCE'].get()),
    }

    analyze_file(file_path, params)

def open_saves():
    save_dir = os.path.join(os.getcwd(), 'save')
    if os.path.exists(save_dir):
        os.startfile(save_dir)
    else:
        messagebox.showerror("Error", "保存先ディレクトリが見つかりません。")

def show_graph(image_path, is_step_response, original_csv_path):
    graph_window = tk.Toplevel()
    graph_window.title("CSV2Graph result")

    img = Image.open(image_path)
    img = img.resize((800, 600), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)

    img_label = tk.Label(graph_window, image=img_tk)
    img_label.image = img_tk  # 参照保持
    img_label.pack(padx=10, pady=10)

    result_text = "STEP RESPONSE DETECTED!" if is_step_response else "NO STEP RESPONSE DETECTED."
    result_label = tk.Label(graph_window, text=result_text, font=("Arial", 14, 'bold'))
    result_label.pack(pady=10)

    def save_graph():
        save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(save_dir, exist_ok=True)

        default_filename = os.path.splitext(os.path.basename(original_csv_path))[0] + ".png"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialfile=default_filename,
            initialdir=save_dir
        )

        if save_path:
            img.save(save_path)
            messagebox.showinfo("Saved", "Graph saved successfully!")

    save_button = tk.Button(graph_window, text="グラフを保存", command=save_graph, font=("Arial", 14))
    save_button.pack(pady=10)

    close_button = tk.Button(graph_window, text="閉じる", command=graph_window.destroy, font=("Arial", 14))
    close_button.pack(pady=10)

def main_gui():
    root = tk.Tk()
    root.title("CSV2Graph Setting")

    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)

    sections = {
        "【データに関する設定】": ['TIME_COL', 'VOLTAGE_COL', 'SKIP_ROWS'],
        "【解析に関する設定】": ['MOVING_AVERAGE_WINDOW', 'VOLTAGE_TOLERANCE', 'PLOT_RANGE_MIN', 'PLOT_RANGE_MAX'],
        "【ステップ応答判別設定】": ['SETTLE_TIME', 'SETTLE_TOLERANCE', 'PEAK_TOLERANCE']
    }
    default_values = {
        'TIME_COL': 'Date/Time',
        'VOLTAGE_COL': 'No.2',
        'SKIP_ROWS': '1, 2',
        'MOVING_AVERAGE_WINDOW': '5',
        'VOLTAGE_TOLERANCE': '0.02',
        'PLOT_RANGE_MIN': '0',
        'PLOT_RANGE_MAX': '5',
        'SETTLE_TIME': '2.0',
        'SETTLE_TOLERANCE': '0.05',
        'PEAK_TOLERANCE': '0.3'
    }

    descriptions = {
        'TIME_COL': "時刻の列名",
        'VOLTAGE_COL': "電圧の列名",
        'SKIP_ROWS': "スキップする行番号（例: 1, 2）",
        'MOVING_AVERAGE_WINDOW': "移動平均の窓幅",
        'VOLTAGE_TOLERANCE': "電圧変化検出の閾値 [V]",
        'PLOT_RANGE_MIN': "グラフ表示範囲（最小時間）[s]",
        'PLOT_RANGE_MAX': "グラフ表示範囲（最大時間）[s]",
        'SETTLE_TIME': "定常判定開始時間 [s]",
        'SETTLE_TOLERANCE': "定常状態の許容標準偏差 [V]",
        'PEAK_TOLERANCE': "ジャンプ検出閾値 [V]"
    }

    entries = {}

    for section, keys in sections.items():
        section_label = tk.Label(frame, text=section, font=("Arial", 14, 'bold'))
        section_label.pack(pady=(10, 0))

        for key in keys:
            row = tk.Frame(frame)
            label = tk.Label(row, text=descriptions[key], width=30, anchor='w')
            entry = tk.Entry(row)
            entry.insert(0, default_values[key])
            row.pack(side=tk.TOP, fill=tk.X, pady=5)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            entries[key] = entry

    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)

    button = tk.Button(button_frame, text="CSVファイルを選択して解析", font=("Arial", 14),
                       command=lambda: select_file_and_analyze(entries), width=30)
    button.grid(row=0, column=0, pady=5, padx=5)

    open_button = tk.Button(button_frame, text="保存したグラフ", font=("Arial", 14),
                            command=lambda: open_saves(), width=30)
    open_button.grid(row=1, column=0, pady=5, padx=5)

    root.mainloop()

if __name__ == "__main__":
    main_gui()