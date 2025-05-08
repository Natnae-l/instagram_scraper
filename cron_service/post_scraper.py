import datetime
import schedule
import time
import random
import concurrent.futures
from rocketapi import InstagramAPI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.db import instagram_posts, instagram_users
from config.environments import settings
from schemas.instagram_users import UserBase
from typing import List

# Initialize API and database connection
instagram_api = InstagramAPI(token=settings.ROCKET_API_TOKEN)
posts_collection = instagram_posts


@retry(
    stop=stop_after_attempt(settings.MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=60),
    retry=retry_if_exception_type((Exception,)),  # Retry on any exception
    before_sleep=lambda retry_state: print(
        f"Retry {retry_state.attempt_number} for {retry_state.args[0]} "
        f"after error: {str(retry_state.outcome.exception())}"
    )
)
def get_and_save_post_data(instagram_id):
    max_pages = getattr(settings, 'MAX_PAGES', 10)
    count_per_page = getattr(settings, 'COUNT_PER_PAGE', 20)

    try:
        print(f"Starting scrape for account ID: {instagram_id}")
        max_id = None
        pages_processed = 0
        posts_inserted = 0

        while pages_processed < max_pages:
            try:
                # Randomized rate limiting
                # Random delay between 1-3 seconds
                time.sleep(random.uniform(1, 3))

                response = instagram_api.get_user_media(
                    instagram_id,
                    count=count_per_page,
                    max_id=max_id
                )

                if not response:
                    print(f"Empty response for ID: {instagram_id}")
                    break

                if 'items' not in response:
                    if response.get('status') == 'fail':
                        raise Exception(
                            f"API failure: {response.get('message')}")
                    break

                posts = response.get('items', [])
                if not posts:
                    break

                new_posts = []
                for post in posts:
                    try:
                        post_id = post.get('id', '')
                        if not post_id:
                            continue

                        actual_post_id, user_id = post_id.split('_', 1)

                        if posts_collection.find_one({"post_id": actual_post_id}):
                            print(f"Post {actual_post_id} already exists")
                            continue  # Skip but continue with other posts

                        media_urls = extract_media_urls(post)

                        new_posts.append({
                            "post_id": actual_post_id,
                            "instagram_id": instagram_id,
                            "username": post.get('user', {}).get('username', ''),
                            "taken_at": datetime.datetime.utcfromtimestamp(
                                post.get('taken_at', 0)
                            ),
                            "caption": post.get('caption', {}).get('text', ''),
                            "media_type": post.get('media_type', ''),
                            "like_count": post.get('like_count', 0),
                            "comment_count": post.get('comment_count', 0),
                            "media_urls": media_urls,
                            "created_at": datetime.datetime.utcnow()
                        })

                    except Exception as e:
                        print(f"Error processing post {post_id}: {str(e)}")
                        continue

                if new_posts:
                    try:
                        posts_collection.insert_many(new_posts)
                        posts_inserted += len(new_posts)
                        print(
                            f"Inserted {len(new_posts)} posts for {instagram_id}")
                    except Exception as e:
                        print(f"DB insert error: {str(e)}")
                        # Retry just this batch if needed
                        raise

                if not response.get('more_available', False):
                    break

                max_id = response.get('next_max_id')
                if not max_id:
                    break

                pages_processed += 1

            except Exception as e:
                print(f"Error fetching page: {str(e)}")
                if pages_processed == 0:  # Only retry if no pages were processed yet
                    raise
                break  # Continue to next page if we already have some data

        return posts_inserted

    except Exception as e:
        print(f"Critical error for {instagram_id}: {str(e)}")
        raise  # This will trigger the retry decorator


def scrape_instagram_posts():
    """Scrape posts for all users using multithreading"""
    users_cursor = instagram_users.aggregate([
        {"$match": {"scrape": True, "instagram_id": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$instagram_id", "user": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$user"}}
    ])

    users_to_scrape = list(users_cursor)
    if not users_to_scrape:
        print("No users to scrape")
        return

    print(f"Starting scrape for {len(users_to_scrape)} accounts")

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_THREADS) as executor:
        # Submit all scraping tasks
        future_to_user = {
            executor.submit(get_and_save_post_data, user['instagram_id']): user['instagram_id']
            for user in users_to_scrape
        }

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_user):
            instagram_id = future_to_user[future]
            try:
                posts_inserted = future.result()
                print(
                    f"Completed {instagram_id}: {posts_inserted} posts inserted")
            except Exception as e:
                print(f"Error scraping {instagram_id}: {str(e)}")


def extract_media_urls(post):
    media_urls = []
    try:
        items = post.get('carousel_media', [post])
        for item in items:
            if item['media_type'] == 1:  # Image
                media_urls.append(item['image_versions2']
                                  ['candidates'][0]['url'])
            elif item['media_type'] == 2 and 'video_versions' in item:  # Video
                media_urls.append(item['video_versions'][0]['url'])
    except Exception as e:
        print(f"Error extracting media: {str(e)}")
    return media_urls


schedule.every(settings.RUN_INTERVAL_PER_MINUTE).minutes.do(
    scrape_instagram_posts)
