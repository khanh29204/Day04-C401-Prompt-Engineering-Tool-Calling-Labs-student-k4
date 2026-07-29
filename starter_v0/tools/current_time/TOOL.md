---
name: current_time
track: core
kind: live_api
provider: TimeAPI
requires_env: []
inputs: [timezone]
outputs: [datetime, date, time, timezone, day_of_week]
side_effect: false
---
# current_time

Lấy thời gian hiện tại từ API theo múi giờ, mặc định là Asia/Ho_Chi_Minh (Việt Nam).
