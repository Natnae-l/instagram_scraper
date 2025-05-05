import datetime
import schedule
import time
from rocketapi import InstagramAPI
from config.db import instagram_posts, instagram_users
from config.environments import settings
from schemas.instagram_users import UserBase

# Initialize API and database connection
instagram_api = InstagramAPI(token= settings.ROCKET_API_TOKEN)
posts_collection = instagram_posts

def get_and_save_post_data(instagram_id):
    max_pages = settings.MAX_PAGES
    count_per_page = settings.COUNT_PER_PAGE

    try:
        print(f"Attempting to scrape posts for account with ID: {instagram_id}")
        max_id = None
        pages_processed = 0
        posts_inserted = 0

        while pages_processed < max_pages:
            try:
                # Add rate limiting
                time.sleep(2)  # Be gentle with the API
                
                response = instagram_api.get_user_media(
                    instagram_id, 
                    count=count_per_page, 
                    max_id=max_id
                )
                
                if not response or 'items' not in response:
                    print(f"Bad response for ID: {instagram_id}")
                    break

                posts = response['items']
                if not posts:
                    break

                new_posts = []
                for post in posts:
                    try:
                        post_id = post['id']
                        actual_post_id, user_id = post_id.split('_')

                        if posts_collection.find_one({"post_id": actual_post_id}):
                            print(f"Found existing post: {actual_post_id}")
                            return posts_inserted  # Return count of inserted posts

                        media_urls = extract_media_urls(post)
                        
                        new_posts.append({
                            "post_id": actual_post_id,
                            "instagram_id": instagram_id,
                            "username": post['user']['username'],
                            "taken_at": datetime.datetime.utcfromtimestamp(post['taken_at']),
                            "caption": post['caption']['text'] if post.get('caption') else '',
                            "media_type": post['media_type'],
                            "like_count": post['like_count'],
                            "comment_count": post['comment_count'],
                            "media_urls": media_urls,
                            "created_at": datetime.datetime.utcnow()
                        })

                    except Exception as e:
                        print(f"Error processing post {post_id}: {str(e)}")
                        continue

                if new_posts:
                    posts_collection.insert_many(new_posts)
                    posts_inserted += len(new_posts)
                    print(f"Inserted {len(new_posts)} new posts")

                if not response.get('more_available', False):
                    break

                max_id = response.get('next_max_id')
                if not max_id:
                    break

                pages_processed += 1

            except Exception as e:
                print(f"Error fetching page: {str(e)}")
                break

        return posts_inserted

    except Exception as e:
        print(f"Critical error for {instagram_id}: {str(e)}")
        return 0

def scrape_instagram_posts():
    users: list[UserBase] = list(instagram_users.find())
    for user in users:
        if hasattr(user, 'scrape') and hasattr(user, 'instagram_id'):
            if user.scrape and user.instagram_id:
                 get_and_save_post_data(user.instagram_id)

def extract_media_urls(post):
    media_urls = []
    try:
        items = post.get('carousel_media', [post])
        for item in items:
            if item['media_type'] == 1:  # Image
                media_urls.append(item['image_versions2']['candidates'][0]['url'])
            elif item['media_type'] == 2 and 'video_versions' in item:  # Video
                media_urls.append(item['video_versions'][0]['url'])
    except Exception as e:
        print(f"Error extracting media: {str(e)}")
    return media_urls


schedule.every(settings.RUN_INTERVAL_PER_MINUTE).minutes.do(scrape_instagram_posts)

