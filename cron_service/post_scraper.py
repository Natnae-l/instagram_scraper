import datetime
import schedule
import time
from rocketapi import InstagramAPI
from config.db import instagram_posts

# Initialize API and database connection
instagram_api = InstagramAPI(token="QA4aCgeWEgkbt99CI2toIA")
posts_collection = instagram_posts


def get_and_save_post_data(instagram_id):
    try:
        print(f"Attempting to scrape posts for account with ID: {instagram_id}")

        max_id = None

        while True:
            try:
                response = instagram_api.get_user_media(instagram_id, count=50, max_id=max_id)
                if not response or 'items' not in response:
                    print(f"Bad response from RocketAPI for account with ID: {instagram_id}. Continuing with next post.")
                    max_id = None  # Reset max_id to continue fetching posts
                    continue

                posts = response['items']
                if not posts:
                    break

                for post in posts:
                    try:
                        post_id = post['id']

                        # Split post_id to get the actual post ID and user ID
                        actual_post_id, user_id = post_id.split('_')

                        # Check if the post already exists in the database
                        existing_post = posts_collection.find_one({"post_id": actual_post_id})
                        if existing_post:
                            print(f"Found existing post with ID: {actual_post_id}. Stopping further scraping for this profile.")
                            return  # Stop the scraping process for the current profile if an existing post is found

                        # Handle different media types and structures
                        media_urls = []
                        if 'carousel_media' in post:
                            # Carousel post, handle multiple media items
                            for item in post['carousel_media']:
                                media_type = item['media_type']
                                if media_type == 1:  # Image
                                    media_urls.append(item['image_versions2']['candidates'][0]['url'])
                                elif media_type == 2:  # Video
                                    if 'video_versions' in item:
                                        media_urls.append(item['video_versions'][0]['url'])
                        else:
                            # Single media post
                            media_type = post['media_type']
                            if media_type == 1:  # Image
                                if 'image_versions2' in post:
                                    media_urls.append(post['image_versions2']['candidates'][0]['url'])
                            elif media_type == 2:  # Video
                                if 'video_versions' in post:
                                    media_urls.append(post['video_versions'][0]['url'])

                        # Post is new, so extract details and store it
                        post_data = {
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
                        }

                        posts_collection.insert_one(post_data)
                        print(f"Inserted new post with ID: {actual_post_id}")

                    except Exception as e:
                        # Log the error and continue with the next post
                        print(f"There was an error while processing post ID: {post_id} for account with ID: {instagram_id}: {e}")
                        continue

                # Check if there are more posts to fetch
                more_available = response.get('more_available', False)
                if not more_available:
                    break

                # Update max_id to fetch the next set of posts
                max_id = response.get('next_max_id')
                if not max_id:
                    break

            except Exception as e:
                print(f"There was an error fetching posts for account with ID: {instagram_id}: {e}")
                max_id = None  # Reset max_id to continue with the next posts
                continue  # Continue fetching the next batch of posts

    except Exception as e:
        print(f"There was a critical error while extracting data for account with ID: {instagram_id}: {e}")

schedule.every(1).minutes.do(get_and_save_post_data)


while True:
    schedule.run_pending()
    time.sleep(1)

