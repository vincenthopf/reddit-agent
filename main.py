import praw
from random import randint, uniform
from time import sleep
from praw.exceptions import RedditAPIException
from generator_comment import GeneratorCommentGPT
from comment_storage import CommentStorage
import config
import time
from datetime import datetime, timedelta
import re

print("[DEBUG] Initializing Reddit API client...")
print(f"[DEBUG] Username: {config.REDDIT_USERNAME}")
print(f"[DEBUG] Client ID: {config.REDDIT_CLIENT_ID[:8]}...")
print(f"[DEBUG] User agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    username=config.REDDIT_USERNAME,
    password=config.REDDIT_PASSWORD,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
)

try:
    print(f"[DEBUG] Testing Reddit authentication...")
    user = reddit.user.me()
    print(f"[SUCCESS] Authenticated as: {user.name}")
    print(f"[DEBUG] Account karma: {user.link_karma + user.comment_karma}")
    print(f"[DEBUG] Account created: {user.created_utc}")
    print(f"[DEBUG] Account verified: {user.verified}")
    
    # Test basic subreddit access
    print(f"[DEBUG] Testing basic subreddit access...")
    try:
        test_sub = reddit.subreddit("python")
        test_post = next(test_sub.hot(limit=1))
        print(f"[SUCCESS] Can access r/python - latest post: {test_post.title[:50]}...")
    except Exception as sub_e:
        print(f"[ERROR] Cannot access r/python: {sub_e}")
        
except Exception as e:
    print(f"[ERROR] Authentication failed: {e}")
    print(f"[DEBUG] Exception type: {type(e).__name__}")
    if hasattr(e, 'response'):
        print(f"[DEBUG] HTTP status code: {getattr(e.response, 'status_code', 'N/A')}")
        print(f"[DEBUG] Response headers: {getattr(e.response, 'headers', 'N/A')}")
        print(f"[DEBUG] Response text: {getattr(e.response, 'text', 'N/A')[:500]}")
    
    print(f"\n[TROUBLESHOOTING] Possible issues:")
    print(f"1. Account may be shadowbanned or suspended")
    print(f"2. API credentials may be invalid or expired")
    print(f"3. IP address may be blocked by Reddit")
    print(f"4. Rate limits exceeded")
    print(f"5. Reddit API may be experiencing issues")
    print(f"\nTry:")
    print(f"- Check if you can log into Reddit manually")
    print(f"- Verify API credentials in Reddit app settings")
    print(f"- Try from a different IP/VPN")
    print(f"- Wait a few hours and try again")

def find_single_post(reddit, commented_posts):
    print("[INFO] Searching for a new post to comment on...")
    subreddits = ["AITAH"]
    
    current_time = time.time()
    max_age = 7200  # 2 hours
    
    # Shuffle subreddits to vary search order
    from random import shuffle
    shuffled_subreddits = subreddits.copy()
    shuffle(shuffled_subreddits)
    
    print(f"[INFO] Checking subreddits in random order...")
    
    for i, subreddit_name in enumerate(shuffled_subreddits, 1):
        try:
            print(f"       [{i}/{len(shuffled_subreddits)}] Checking r/{subreddit_name}...")
            print(f"       [DEBUG] Attempting to access subreddit: {subreddit_name}")
            subreddit = reddit.subreddit(subreddit_name)
            print(f"       [DEBUG] Subreddit object created, fetching new posts...")
            for submission in subreddit.new(limit=25):
                age_hours = (current_time - submission.created_utc) / 3600
                if (submission.id not in commented_posts and 
                    current_time - submission.created_utc < max_age and
                    len(submission.selftext) > 100):
                    print(f"       [FOUND] Eligible post in r/{subreddit_name} (age: {age_hours:.1f}h)")
                    return submission
            print(f"       [SKIP] No eligible posts in r/{subreddit_name}")
        except Exception as e:
            print(f"       [ERROR] Error accessing r/{subreddit_name}: {e}")
            print(f"       [DEBUG] Exception type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"       [DEBUG] HTTP status code: {getattr(e.response, 'status_code', 'N/A')}")
                print(f"       [DEBUG] Response headers: {getattr(e.response, 'headers', 'N/A')}")
                print(f"       [DEBUG] Response text: {getattr(e.response, 'text', 'N/A')[:500]}")
            if hasattr(e, 'error_type'):
                print(f"       [DEBUG] Reddit error type: {e.error_type}")
            continue
    
    print(f"\n[INFO] No eligible posts found in any subreddit")
    return None

def extract_text_title(submission):
    return submission.title

def extract_text_content(submission):
    return submission.selftext

def extract_comment_content_and_upvotes(submission):
    submission.comments.replace_more(limit=0)
    comments = submission.comments.list()
    return [(comment.body, comment.score) for comment in comments]

def filter_respectful_language(comment):
    """Filter out disrespectful language from comments"""
    # List of terms to avoid - focusing on condescending/disrespectful terms
    disrespectful_terms = [
        r'\bsweetheart\b', r'\bhoney\b', r'\bdarling\b', r'\bbabe\b', 
        r'\bkiddo\b', r'\bchild\b(?=\s)', r'\bgrow up\b', r'\bimmature\b',
        r'\byoung lady\b', r'\byoung man\b', r'\blittle\s+\w+\b'
    ]
    
    filtered_comment = comment
    
    for term_pattern in disrespectful_terms:
        # Replace with more respectful alternatives
        if re.search(term_pattern, filtered_comment, re.IGNORECASE):
            if 'sweetheart' in term_pattern or 'honey' in term_pattern or 'darling' in term_pattern:
                filtered_comment = re.sub(term_pattern, '', filtered_comment, flags=re.IGNORECASE)
            elif 'kiddo' in term_pattern or 'child' in term_pattern:
                filtered_comment = re.sub(term_pattern, '', filtered_comment, flags=re.IGNORECASE)
            elif 'grow up' in term_pattern:
                filtered_comment = re.sub(term_pattern, 'consider reflecting on this', filtered_comment, flags=re.IGNORECASE)
            elif 'immature' in term_pattern:
                filtered_comment = re.sub(term_pattern, 'this behavior shows room for growth', filtered_comment, flags=re.IGNORECASE)
    
    # Clean up any double spaces or awkward formatting from removals
    filtered_comment = re.sub(r'\s+', ' ', filtered_comment).strip()
    
    return filtered_comment

def generate_comment(chat_llm, title, post_text, comments, subreddit=""):
    try:
        comment = chat_llm.generate_comment(title, post_text, comments, subreddit)
        return filter_respectful_language(comment)
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
        print(f"       [DEBUG] Exception type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"       [DEBUG] HTTP status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"       [DEBUG] Response headers: {getattr(e.response, 'headers', 'N/A')}")
            print(f"       [DEBUG] Response text: {getattr(e.response, 'text', 'N/A')[:500]}")
        if hasattr(e, 'error_type'):
            print(f"       [DEBUG] Reddit error type: {e.error_type}")
    return commented_posts

def pause_randomly():
    sleep_duration = uniform(4 * 60, 10 * 60)  # 4-10 minutes (already within cap)
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

def track_comment_performance(reddit, comment_storage):
    print("\n[TRACKING] Checking comment performance...")
    try:
        stored_count = 0
        checked_count = 0
        current_time = time.time()
        
        for comment in reddit.user.me().comments.new(limit=None):
            checked_count += 1
            comment_age_hours = (current_time - comment.created_utc) / 3600
            
            # Store downvoted comments (but don't delete)
            if comment.score < 0:
                post_url = f"https://reddit.com{comment.submission.permalink}"
                post_title = comment.submission.title[:100] + ("..." if len(comment.submission.title) > 100 else "")
                
                comment_storage.store_comment(
                    comment_id=comment.id,
                    comment_body=comment.body,
                    score=comment.score,
                    post_url=post_url,
                    post_title=post_title,
                    subreddit=str(comment.subreddit),
                    reason="downvoted",
                    age_hours=comment_age_hours
                )
                
                print(f"          [STORE] Storing downvoted comment (ID: {comment.id}, Score: {comment.score}) - NOT DELETING")
                stored_count += 1
            # Store underperforming comments (but don't delete)
            elif comment_age_hours >= 24 and comment.score < 3:
                age_days = int(comment_age_hours // 24)
                age_hours_remaining = int(comment_age_hours % 24)
                
                post_url = f"https://reddit.com{comment.submission.permalink}"
                post_title = comment.submission.title[:100] + ("..." if len(comment.submission.title) > 100 else "")
                
                comment_storage.store_comment(
                    comment_id=comment.id,
                    comment_body=comment.body,
                    score=comment.score,
                    post_url=post_url,
                    post_title=post_title,
                    subreddit=str(comment.subreddit),
                    reason="underperforming",
                    age_hours=comment_age_hours
                )
                
                print(f"          [STORE] Storing underperforming comment (ID: {comment.id}, Score: {comment.score}, Age: {age_days}d {age_hours_remaining}h) - NOT DELETING")
                stored_count += 1
            elif comment_age_hours >= 24:
                # Log well-performing comments for reference
                age_days = int(comment_age_hours // 24)
                age_hours_remaining = int(comment_age_hours % 24)
                print(f"          [KEEP] Good comment (ID: {comment.id}, Score: {comment.score}, Age: {age_days}d {age_hours_remaining}h)")
                
        print(f"          [TRACKING] Checked {checked_count} comments, tracked {stored_count} underperforming ones")
        
        # Display storage stats
        stats = comment_storage.get_stats()
        print(f"          [STATS] Total tracked: {stats['total_stored']}, Downvoted: {stats['downvoted']}, Underperforming: {stats['underperforming']}")
        
    except Exception as e:
        print(f"          [ERROR] Error tracking comments: {e}")

def main():
    print("[SYSTEM] Reddit Agent Starting...")
    print(f"[SYSTEM] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Initialize comment storage system
    comment_storage = CommentStorage()
    print(f"[SYSTEM] Comment storage initialized")
    
    # Initialize AI comment generator
    print(f"[SYSTEM] Initializing AI comment generator...")
    generator_post = GeneratorCommentGPT(openrouter_api_key=config.OPENROUTER_API_KEY)
    print("         [SUCCESS] AI generator ready")
    
    # Load previously commented posts
    commented_posts = get_commented_posts(reddit)
    
    print(f"\n[SYSTEM] Starting continuous search-comment-wait cycle...")
    print("="*50)
    
    cycle_count = 0
    daily_comment_count = 0
    max_daily_comments = 50  # Limit to 50 comments per day
    
    with open("commented_post_links.txt", "a") as file:
        while True:  # Continuous loop
            cycle_count += 1
            print(f"\n[CYCLE {cycle_count}] Starting new search cycle...")
            print(f"[SYSTEM] Daily comments so far: {daily_comment_count}/{max_daily_comments}")
            
            # Check daily limit
            if daily_comment_count >= max_daily_comments:
                print(f"[SYSTEM] Daily comment limit reached ({max_daily_comments}). Sleeping for 12 hours...")
                sleep(12 * 60 * 60)  # Sleep for 12 hours
                daily_comment_count = 0  # Reset counter
                continue
            
            # Search for a single post
            submission = find_single_post(reddit, commented_posts)
            
            if not submission:
                print(f"[CYCLE {cycle_count}] No eligible posts found")
            
            else:
                # Process the found post
                print(f"\n[POST] Processing post:")
                print(f"       Title: {submission.title[:80]}{'...' if len(submission.title) > 80 else ''}")
                print(f"       Subreddit: r/{submission.subreddit}")
                print(f"       Age: {int((time.time() - submission.created_utc) / 3600)}h {int(((time.time() - submission.created_utc) % 3600) / 60)}m")
                
                post_title = extract_text_title(submission)
                text_content = extract_text_content(submission)
                
                print(f"       Post length: {len(text_content)} characters")
                print(f"       [AI] Generating comment...")
                
                comment_content_and_upvotes = extract_comment_content_and_upvotes(submission)
                comment = generate_comment(generator_post, post_title, text_content, comment_content_and_upvotes, str(submission.subreddit))
                
                if comment:
                    print(f"       [AI] Generated comment ({len(comment)} chars)")
                    print(f"       [REDDIT] Posting comment...")
                    
                    # Attempt to post the comment
                    comment_posted = False
                    while not comment_posted:
                        try:
                            response = submission.reply(comment)
                            file.write(f"{response.submission.url}\n")
                            file.flush()  # Ensure it's written immediately
                            comment_posted = True
                            daily_comment_count += 1  # Increment daily counter
                            print(f"       [SUCCESS] Comment posted successfully!")
                            print(f"       [SYSTEM] Daily comment count: {daily_comment_count}/{max_daily_comments}")
                            print(f"\n[POST DETAILS]")
                            print(f"Title: {submission.title}")
                            print(f"URL: {submission.url}")
                            print(f"Subreddit: r/{submission.subreddit}")
                            print(f"\n[COMMENT POSTED]")
                            print(f"{comment}")
                            print(f"\n" + "="*50)
                        except RedditAPIException as e:
                            print(f"       [DEBUG] RedditAPIException details:")
                            print(f"       [DEBUG] Exception items: {e.items}")
                            
                            # Handle rate limiting
                            if any(item.error_type == "RATELIMIT" for item in e.items):
                                # Extract wait time more safely
                                rate_limit_item = next(item for item in e.items if item.error_type == "RATELIMIT")
                                message = rate_limit_item.message
                                try:
                                    # Try to extract minutes from message like "Take a break for 8 minutes"
                                    words = message.split()
                                    if "minutes" in message:
                                        wait_minutes = int([w for w in words if w.isdigit()][-1])
                                    else:
                                        wait_minutes = 10  # Default fallback
                                except:
                                    wait_minutes = 10  # Safe fallback
                                
                                print(f"       [RATELIMIT] Hit rate limit: {message}")
                                print(f"       [RATELIMIT] Waiting {wait_minutes} minutes...")
                                sleep(wait_minutes * 60)
                                
                                # After rate limit, wait even longer before next comment
                                print(f"       [RATELIMIT] Adding extra delay to avoid future rate limits...")
                                sleep(300)  # Extra 5 minutes
                                
                            elif any(item.error_type == "THREAD_LOCKED" for item in e.items):
                                print(f"       [ERROR] Thread locked")
                                comment_posted = True  # Exit the retry loop
                            else:
                                error_types = [item.error_type for item in e.items]
                                print(f"       [ERROR] Reddit API errors: {error_types}")
                                comment_posted = True  # Exit the retry loop
                        except Exception as e:
                            print(f"       [ERROR] Unexpected error posting comment: {e}")
                            print(f"       [DEBUG] Exception type: {type(e).__name__}")
                            if hasattr(e, 'response'):
                                print(f"       [DEBUG] HTTP status code: {getattr(e.response, 'status_code', 'N/A')}")
                                print(f"       [DEBUG] Response headers: {getattr(e.response, 'headers', 'N/A')}")
                                print(f"       [DEBUG] Response text: {getattr(e.response, 'text', 'N/A')[:500]}")
                            comment_posted = True  # Exit the retry loop
                    
                    # Add to commented posts
                    commented_posts.add(submission.id)
                else:
                    print(f"       [ERROR] Failed to generate comment")
            
            # Random chance to track comment performance
            if randint(1, 30) == 1:  # 3.3% chance
                pause_randomly()
                track_comment_performance(reddit, comment_storage)
            
            # Single wait time for all scenarios - increased to avoid rate limits
            sleep_duration = randint(600, 1200)  # 10-20 minutes
            minutes = sleep_duration // 60
            seconds = sleep_duration % 60
            next_time = datetime.now() + timedelta(seconds=sleep_duration)
            
            print(f"\n[WAIT] Waiting {minutes}m {seconds}s before next search...")
            print(f"       Next search at: {next_time.strftime('%H:%M:%S')}")
            
            sleep(sleep_duration)

if __name__ == "__main__":
    main()
