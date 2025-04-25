#csv2graph.py
import pandas as pd
import matplotlib.pyplot as plt
import os

#path setting
data_filename = '0-40.csv'
data_dir = os.path.join(os.path.dirname(__file__), 'data')
save_dir = os.path.join(os.path.dirname(__file__), 'save')
csv_path = os.path.join(data_dir, data_filename)
output_filename = os.path.splitext(data_filename)[0] + '.png'
output_path = os.path.join(save_dir, output_filename)

#import CSV
df = pd.read_csv(csv_path, skiprows=2)

#convert date to time
time = pd.to_datetime(df['Date/Time'])
time_zeroed = (time - time.iloc[0]).dt.total_seconds()

#choice voltage data
voltage =df['No.2']
voltage_zeroed = voltage - voltage.iloc[0]

#set time range
start_time = 0
end_time = 5
mask = (time_zeroed >= start_time)&(time_zeroed <= end_time)

#draw graph
plt.figure(figsize=(10,5))
plt.plot(time_zeroed[mask],voltage_zeroed[mask],label='voltage over time')
plt.xlabel('Time[s]')
plt.ylabel('Voltage[V]')
plt.title('V-t graph zeroed')
plt.grid(True)
plt.legend()
plt.tight_layout()

#export graph
os.makedirs(save_dir, exist_ok=True)
plt.savefig(output_path,dpi=300)
plt.close()
print(f"File saved as '{output_filename}'.")