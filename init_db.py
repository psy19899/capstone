from bots.crawler import * 

"""
dates = ['20240517', '20240518', '20240519', '20240520', '20240521']
for date_ in dates: 
    Crawler_News(modes='date-specific', dates_to_visit=[date_]).fetch()

save_db_to_fs('news')
"""

Crawler_Players().fetch()

Crawler_News().fetch()

Crawler_Calendars().fetch()

Crawler_Stats().fetch()

"""
import os 
os.execvp("gunicorn", ["gunicorn", "-w", "5", "-b", "0.0.0.0:5000", "main:app"])
"""