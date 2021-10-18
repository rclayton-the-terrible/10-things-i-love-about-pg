from metar import Metar
from functools import reduce
obs = Metar.Metar('KSAN 101651Z 21005KT 10SM CLR 21/13 A3006 RMK AO2 SLP177 T02110128')
print({
  "id": 0,
  "time": obs.time.strftime('%Y-%m-%dT%H:%M:%S%zZ'),
  "station_id": obs.station_id,
  "temperature": obs.temp.value(),
  "dewpoint": obs.dewpt.value(),
  "wind_dir": obs.wind_dir.value() if obs.wind_dir else None,
  "wind_gust": obs.wind_gust.value() if obs.wind_gust else None,
  "wind_speed": obs.wind_speed.value() if obs.wind_speed else None,
  "altimeter": obs.press.value(),
  "ob_type": obs.type,
  "visibility": obs.vis.value() if obs.vis else None,
  "clouds": "%s" % obs.sky,
  "sig_weather": "%s" % obs.weather,
  "sea_level_pressure": obs.press_sea_level.value() if obs.press_sea_level else None,
  "remarks": obs.remarks(),
})
