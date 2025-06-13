import praw
from random import randint, uniform
from time import sleep
from praw.exceptions import RedditAPIException
from generator_comment import GeneratorCommentGPT
import config
import time
from datetime import datetime, timedelta

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    username=config.REDDIT_USERNAME,
    password=config.REDDIT_PASSWORD,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
)

def get_trending_topics(reddit, commented_posts):
    print("[INFO] Searching for new posts...")
    trending_topics = []
    subreddits = ["AITAH", "AmItheAsshole", "relationship_advice", "relationships", "offmychest", "TrueOffMyChest", "confession"]
    
    current_time = time.time()
    max_age = 7200  # 2 hours
    
    print(f"[INFO] Checking {len(subreddits)} subreddits: {', '.join(subreddits)}")
    
    for i, subreddit_name in enumerate(subreddits, 1):
        try:
            print(f"       [{i}/{len(subreddits)}] Checking r/{subreddit_name}...")
            posts_found = 0
            for submission in reddit.subreddit(subreddit_name).new(limit=25):
                age_hours = (current_time - submission.created_utc) / 3600
                if (submission.id not in commented_posts and 
                    current_time - submission.created_utc < max_age and
                    len(submission.selftext) > 100):
                    trending_topics.append(submission)
                    posts_found += 1
            print(f"       [SUCCESS] Found {posts_found} eligible posts")
        except Exception as e:
            print(f"       [ERROR] Error accessing r/{subreddit_name}: {e}")
            continue
    
    print(f"\n[INFO] Total eligible posts found: {len(trending_topics)}")
    return trending_topics

def extract_text_title(submission):
    return submission.title

def extract_text_content(submission):
    return submission.selftext

def extract_comment_content_and_upvotes(submission):
    submission.comments.replace_more(limit=0)
    comments = submission.comments.list()
    return [(comment.body, comment.score) for comment in comments]

def generate_comment(chat_llm, title, post_text, comments, subreddit=""):
    try:
        return chat_llm.generate_comment(title, post_text, comments, subreddit)
    except Exception as e:
        print(f"      [ERROR] Comment generation failed: {e}")
        return ""

def get_commented_posts(reddit):
    print("[INFO] Loading previously commented posts...")
    commented_posts = set()
    try:
        comment_count = 0
        for comment in reddit.user.me().comments.new(limit=1000):
            commented_posts.add(comment.submission.id)
            comment_count += 1
        print(f"       [SUCCESS] Found {comment_count} previous comments, {len(commented_posts)} unique posts")
    except Exception as e:
        print(f"       [ERROR] Error retrieving comments: {e}")
    return commented_posts

def pause_randomly():
    sleep_duration = uniform(4 * 60, 10 * 60)
    minutes = int(sleep_duration // 60)
    seconds = int(sleep_duration % 60)
    end_time = datetime.now() + timedelta(seconds=sleep_duration)
    
    print(f"\n[BREAK] Taking extended break: {minutes}m {seconds}s")
    print(f"        Will resume at: {end_time.strftime('%H:%M:%S')}")
    
    # Show countdown every 30 seconds
    while sleep_duration > 0:
        if sleep_duration > 30:
            sleep(30)
            sleep_duration -= 30
            remaining_mins = int(sleep_duration // 60)
            remaining_secs = int(sleep_duration % 60)
            print(f"        [BREAK] {remaining_mins}m {remaining_secs}s remaining...")
        else:
            sleep(sleep_duration)
            sleep_duration = 0
    
    print("        [BREAK] Break complete, resuming...")

def delete_underperforming_comments(reddit):
    print("\n[CLEANUP] Checking for underperforming comments to delete...")
    try:
        deleted_count = 0
        checked_count = 0
        current_time = time.time()
        
        for comment in reddit.user.me().comments.new(limit=None):
            checked_count += 1
            comment_age_hours = (current_time - comment.created_utc) / 3600
            
            # Delete if downvoted (negative score)
            if comment.score < 0:
                print(f"          [DELETE] Removing downvoted comment (ID: {comment.id}, Score: {comment.score})")
                comment.delete()
                deleted_count += 1
            # Delete if older than 24 hours and has less than 3 upvotes
            elif comment_age_hours >= 24 and comment.score < 3:
                age_days = int(comment_age_hours // 24)
                age_hours_remaining = int(comment_age_hours % 24)
                print(f"          [DELETE] Removing underperforming comment (ID: {comment.id}, Score: {comment.score}, Age: {age_days}d {age_hours_remaining}h)")
                comment.delete()
                deleted_count += 1
            elif comment_age_hours >= 24:
                # Log well-performing comments for reference
                age_days = int(comment_age_hours // 24)
                age_hours_remaining = int(comment_age_hours % 24)
                print(f"          [KEEP] Good comment (ID: {comment.id}, Score: {comment.score}, Age: {age_days}d {age_hours_remaining}h)")
                
        print(f"          [CLEANUP] Checked {checked_count} comments, deleted {deleted_count} underperforming ones")
    except Exception as e:
        print(f"          [ERROR] Error deleting comments: {e}")

def main():
    print("[SYSTEM] Reddit Agent Starting...")
    print(f"[SYSTEM] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    commented_posts = get_commented_posts(reddit)
    trending_topics = get_trending_topics(reddit, commented_posts)
    
    if not trending_topics:
        print("\n[ERROR] No eligible posts found. Exiting.")
        return
    
    print(f"\n[SYSTEM] Initializing AI comment generator...")
    generator_post = GeneratorCommentGPT(openrouter_api_key=config.OPENROUTER_API_KEY)
    print("         [SUCCESS] AI generator ready")
    
    print(f"\n[SYSTEM] Starting to process {len(trending_topics)} posts...")
    print("="*50)
    
    with open("commented_post_links.txt", "a") as file:
        for i, submission in enumerate(trending_topics, 1):
            print(f"\n[POST] [{i}/{len(trending_topics)}] Processing post:")
            print(f"        Title: {submission.title[:80]}{'...' if len(submission.title) > 80 else ''}")
            print(f"        Subreddit: r/{submission.subreddit}")
            print(f"        Age: {int((time.time() - submission.created_utc) / 3600)}h {int(((time.time() - submission.created_utc) % 3600) / 60)}m")
            
            post_title = extract_text_title(submission)
            text_content = extract_text_content(submission)
            
            print(f"        Post length: {len(text_content)} characters")
            print(f"        [AI] Generating comment...")
            
            comment_content_and_upvotes = extract_comment_content_and_upvotes(submission)
            comment = generate_comment(generator_post, post_title, text_content, comment_content_and_upvotes, str(submission.subreddit))
            
            if not comment:
                print(f"        [ERROR] Failed to generate comment, skipping")
                continue
            
            print(f"        [AI] Generated comment ({len(comment)} chars)")
            print(f"        [REDDIT] Posting comment...")
            
            exit = False
            while not exit:
                try:
                    response = submission.reply(comment)
                    file.write(f"{response.submission.url}\n")
                    exit = True
                    print(f"        [SUCCESS] Comment posted successfully!")
                    print(f"\n[POST DETAILS]")
                    print(f"Title: {submission.title}")
                    print(f"URL: {submission.url}")
                    print(f"Subreddit: r/{submission.subreddit}")
                    print(f"\n[COMMENT POSTED]")
                    print(f"{comment}")
                    print(f"\n" + "="*50)
                except RedditAPIException as e:
                    if e.error_type == "RATELIMIT":
                        wait_minutes = int(e.message.split(" ")[-5])
                        print(f"        [RATELIMIT] Waiting {wait_minutes} minutes...")
                        sleep(wait_minutes * 60)
                    elif e.error_type == "THREAD_LOCKED":
                        print(f"        [ERROR] Thread locked, skipping")
                        exit = True
                    else:
                        print(f"        [ERROR] {e.error_type}")
                        exit = True
            
            commented_posts.add(submission.id)
            
            # Determine next action
            if i < len(trending_topics):  # Not the last post
                if randint(1, 30) == 1:  # 3.3% chance
                    pause_randomly()
                    delete_underperforming_comments(reddit)
                else:
                    sleep_duration = randint(10, 400)
                    minutes = sleep_duration // 60
                    seconds = sleep_duration % 60
                    next_time = datetime.now() + timedelta(seconds=sleep_duration)
                    
                    print(f"\n[WAIT] Waiting {minutes}m {seconds}s before next post...")
                    print(f"       Next comment at: {next_time.strftime('%H:%M:%S')}")
                    
                    # Show countdown for longer waits
                    if sleep_duration > 60:
                        while sleep_duration > 0:
                            if sleep_duration > 30:
                                sleep(30)
                                sleep_duration -= 30
                                remaining_mins = sleep_duration // 60
                                remaining_secs = sleep_duration % 60
                                print(f"       [WAIT] {remaining_mins}m {remaining_secs}s remaining...")
                            else:
                                sleep(sleep_duration)
                                sleep_duration = 0
                    else:
                        sleep(sleep_duration)
    
    print(f"\n[SYSTEM] Finished processing all posts!")
    print(f"[SYSTEM] Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

if __name__ == "__main__":
    main()
