import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# --- 設定 ---
CSV_FILENAME = 'genkaikando.csv'
TIME_COL = 'Date/Time'
VOLTAGE_COL = 'No.2'
SKIP_ROWS = [1, 2]
MOVING_AVERAGE_WINDOW = 5   # 移動平均の窓幅
VOLTAGE_TOLERANCE = 0.02    # ベースライン判定用の電圧許容範囲 [V]
PLOT_RANGE = (-1, 5)        # 描画する時間範囲 [s]

# ステップ応答判別用
SETTLE_TIME = 2.0           # 定常性確認を開始する時間 [s]
SETTLE_TOLERANCE = 0.05     # 定常状態とみなす標準偏差の許容範囲 [V]
PEAK_TOLERANCE = 0.3       # オーバーシュート・アンダーシュートとみなす変動量 [V]

def detect_step_response(time_shifted, voltage_smoothed, settle_time=SETTLE_TIME, settle_tolerance=SETTLE_TOLERANCE, peak_tolerance=PEAK_TOLERANCE):
    """
    時間0直後にオーバーシュートまたはアンダーシュートがあるか
    その後、定常状態に落ち着くか
    """
    positive_time_mask = time_shifted >= 0
    time_pos = time_shifted[positive_time_mask]
    voltage_pos = voltage_smoothed[positive_time_mask]

    if len(voltage_pos) == 0:
        print("[WARN] No data after time zero.")
        return False

    initial_voltage = voltage_pos.iloc[0]    # 時間0時点の電圧

    peak_voltage = np.max(voltage_pos)    # 最大電圧
    bottom_voltage = np.min(voltage_pos)    #最小電圧

    peak_variation = max(abs(peak_voltage - initial_voltage), abs(bottom_voltage - initial_voltage))    # ピークの変動幅

    # ピーク検出
    if peak_variation < peak_tolerance:
        print("[INFO] No significant overshoot or undershoot detected.")
        return False

    # 定常性確認（一定時間以降）
    settle_mask = (time_pos >= settle_time)
    voltage_settled = voltage_pos[settle_mask]

    if len(voltage_settled) == 0:
        print("[WARN] Not enough data after settle time.")
        return False

    std_settled = voltage_settled.std()

    if std_settled < settle_tolerance:
        print(f"[INFO] Step response detected (std after settle: {std_settled:.4f} V)")
        return True
    else:
        print(f"[INFO] No steady state detected (std after settle: {std_settled:.4f} V)")
        return False

def main():
    # --- フォルダ設定 ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
    data_dir = os.path.join(script_dir, 'data')
    save_dir = os.path.join(script_dir, 'save')
    os.makedirs(save_dir, exist_ok=True)

    # --- データ読み込み ---
    csv_path = os.path.join(data_dir, CSV_FILENAME)
    df = pd.read_csv(csv_path, skiprows=SKIP_ROWS)

    time = pd.to_datetime(df[TIME_COL])
    time_seconds = (time - time.iloc[0]).dt.total_seconds()
    voltage = df[VOLTAGE_COL].astype(float)

    # --- 移動平均 ---
    voltage_smoothed = voltage.rolling(window=MOVING_AVERAGE_WINDOW, center=True, min_periods=1).mean()

    # --- ベースライン探し ---
    baseline_voltage = voltage_smoothed.iloc[0]
    origin_index = None

    for i in range(1, len(voltage_smoothed)):
        if abs(voltage_smoothed.iloc[i] - baseline_voltage) > VOLTAGE_TOLERANCE:
            origin_index = i
            break

    if origin_index is not None:
        origin_time = time_seconds.iloc[origin_index]
        baseline_voltage = voltage_smoothed.iloc[origin_index]
    else:
        origin_time = time_seconds.iloc[0]
        origin_index = 0

    print(f"[INFO] Origin determined at index {origin_index}, time {origin_time:.4f} s")

    # --- 原点補正 ---
    time_shifted = time_seconds - origin_time
    voltage_shifted = voltage

    # --- ステップ応答判別---
    is_step_response = detect_step_response(time_shifted, voltage_smoothed)

    if is_step_response:
        print("[RESULT] This data shows a STEP RESPONSE.")
    else:
        print("[RESULT] This data DOES NOT show a step response.")

    # --- グラフ描画 ---
    mask = (time_shifted >= PLOT_RANGE[0]) & (time_shifted <= PLOT_RANGE[1])

    plt.figure(figsize=(10, 5))
    plt.plot(time_shifted[mask], voltage_shifted[mask], label='Voltage')
    plt.xlabel('Time [s]')
    plt.ylabel('Voltage [V]')
    plt.title('V-t Graph (Zeroed)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # 保存
    output_path = os.path.join(save_dir, os.path.splitext(CSV_FILENAME)[0] + '.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[INFO] Graph saved: {output_path}")

if __name__ == "__main__":
    main()
