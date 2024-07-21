import time
from datetime import datetime

# 現在の標準時間を取得し、小数点以下の秒を表示しないようにフォーマット
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 標準時間を出力
print(current_time)

# 現在のUNIX時間を取得
current_unix_time = int(time.time())

# UNIX時間を出力
print(current_unix_time)

# UNIX時間を'%Y-%m-%d %H:%M:%S'の形式に変換
formatted_unix_time = datetime.fromtimestamp(current_unix_time).strftime('%Y-%m-%d %H:%M:%S')

# 変換した時間を出力
print(formatted_unix_time)

# formatted_unix_timeをUNIX時間に変換
converted_unix_time = int(time.mktime(datetime.strptime(formatted_unix_time, '%Y-%m-%d %H:%M:%S').timetuple()))

# 変換したUNIX時間を出力
print(converted_unix_time)
