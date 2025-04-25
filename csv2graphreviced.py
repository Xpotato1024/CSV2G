import pandas as pd
import numpy as np
import matplotlib.pyplot as pltimport os
import sys

# ベースライン電圧を計算するために使用する最初のデータ点の数 (または秒数)
BASELINE_CALC_POINTS = 20 # 例: 最初の20点で計算 (データ頻度に応じて調整)
# 電圧上昇とみなす閾値 (ベースラインからの上昇分)
VOLTAGE_RISE_THRESHOLD = 0.5 # 例: ベースラインより0.5V上昇したら (実際のデータに合わせて調整)

"""CSVファイルを読み込み、電圧上昇直前を原点としてデータを処理する関数
in: CSVファイルパス、時間列、電圧列、スキップ行数
out: 原点基準変換後の時間(pd.Series)、原点基準変換後の電圧(pd.Series)
"""
def load_and_process_data(csv_path, time_col='Date/Time', voltage_col='No.2', skip_rows=2):
    # CSV読み込みと基本的なエラーチェック
    try:
        df = pd.read_csv(csv_path, skiprows=skip_rows)
        if df.empty:
            print(f"Error: CSV file is empty or contains no data after skipping rows: {csv_path}")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    except Exception as e:        print(f"Error reading CSV file: {e}")
        sys.exit(1)

    if time_col not in df.columns:
        print(f"Error: Time column '{time_col}' not found in {csv_path}")
        sys.exit(1)
    if voltage_col not in df.columns:
        print(f"Error: Voltage column '{voltage_col}' not found in {csv_path}")
        sys.exit(1)

    try:
        # 時間データをdatetimeに変換し、最初の点を0秒とする相対時間に変換
        time = pd.to_datetime(df[time_col])
        time_seconds = (time - time.iloc[0]).dt.total_seconds()
        voltage = df[voltage_col].astype(float)

        # 1. ベースライン電圧の特定
        # 最初のBASELINE_CALC_POINTS点の電圧の中央値を使用
        num_points = min(BASELINE_CALC_POINTS, len(voltage))
        if num_points == 0:
             print(f"Error: Not enough data points ({len(voltage)}) to determine baseline.")
             sys.exit(1)
        baseline_voltage = np.median(voltage.iloc[:num_points])
        print(f"Calculated baseline voltage: {baseline_voltage:.4f} (using first {num_points} points)")

        # 2. 電圧上昇開始点の特定
        # ベースライン + 閾値 を初めて超える点のインデックスを探す
        rise_threshold_value = baseline_voltage + VOLTAGE_RISE_THRESHOLD
        # boolean Seriesを作成 (閾値を超えたらTrue)
        voltage_above_threshold = voltage > rise_threshold_value

        # 最初にTrueになるインデックスを取得
        rise_start_indices = voltage_above_threshold[voltage_above_threshold].index
        if rise_start_indices.empty:
            print(f"Warning: No voltage rise detected above threshold ({rise_threshold_value:.4f}). Using first data point as origin.")
            origin_index = 0
        else:
            first_rise_index = rise_start_indices[0]
            # 上昇開始点の「直前」を原点とする
            origin_index = max(0, first_rise_index - 1) # 最初の点が上昇点だった場合のエッジケース対応
            print(f"Voltage rise detected. First point above threshold at index {first_rise_index}.")
            print(f"Setting origin to index {origin_index}.")

        # 3. 原点の決定
        origin_time = time_seconds.iloc[origin_index]
        origin_voltage = voltage.iloc[origin_index]
        print(f"Origin point: Time={origin_time:.3f}s, Voltage={origin_voltage:.4f}V")

        # 4. データ全体のシフト
        time_origin_based = time_seconds - origin_time
        voltage_origin_based = voltage - origin_voltage

    except Exception as e:
        print(f"Error processing data columns: {e}")
        sys.exit(1)

    return time_origin_based, voltage_origin_based

def plot_and_save_graph(time_data, voltage_data, output_path, start_time=0, end_time=5, dpi=300):
    # 新たに指定した時間範囲でデータをフィルタリング
    mask = (time_data >= start_time) & (time_data <= end_time)

    plt.figure(figsize=(10, 5))
    plt.plot(time_data[mask], voltage_data[mask], label='Voltage Change from Rise Point')
    plt.xlabel('Time from Voltage Rise Start [s]')
    plt.ylabel('Voltage Change [V]')
    plt.title(f'V-t Graph (Origin at Voltage Rise, {start_time}s to {end_time}s)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    save_dir = os.path.dirname(output_path)
    os.makedirs(save_dir, exist_ok=True)

    try:
        plt.savefig(output_path, dpi=dpi)        plt.close()
        print(f"Graph saved successfully to '{output_path}'.")
    except Exception as e:
        print(f"Error saving graph: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # データ設定
    data_filename = '0-40.csv'
		time_column_name = 'Date/Time'
    voltage_column_name = 'No.2'
    csv_skip_rows = 2
		
    # グラフ描画範囲
    plot_start_time = 0
    plot_end_time = 8
    output_dpi = 300

    # パス設定
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    data_dir = os.path.join(script_dir, 'data')
    save_dir = os.path.join(script_dir, 'save')
    csv_path = os.path.join(data_dir, data_filename)
    output_filename = os.path.splitext(data_filename)[0] + '.png'
    output_path = os.path.join(save_dir, output_filename)

    # データの読み込みと処理
    time_processed, voltage_processed = load_and_process_data(
        csv_path,
        time_col=time_column_name,
        voltage_col=voltage_column_name,
        skip_rows=csv_skip_rows
    )

    # グラフの描画と保存
    plot_and_save_graph(
        time_processed,
        voltage_processed,
        output_path,
        start_time=plot_start_time,
        end_time=plot_end_time,
        dpi=output_dpi
    )
