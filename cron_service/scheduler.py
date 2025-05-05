import time
from cron_service.post_scraper import schedule
from config.environments import settings

def run_scheduler():
    
    while True and settings.SCRAPE:
        schedule.run_pending()
        time.sleep(1)

