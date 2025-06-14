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

def find_comments_to_reply_to(reddit, replied_comments):
    """Find high-engagement comments to reply to for deeper interaction"""
    print("[INFO] Searching for comments to reply to...")
    subreddits = ["AITAH"]
    
    current_time = time.time()
    max_age = 3600  # 1 hour for replies (fresher than posts)
    
    from random import shuffle
    shuffled_subreddits = subreddits.copy()
    shuffle(shuffled_subreddits)
    
    for subreddit_name in shuffled_subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Look through recent hot posts for engagement opportunities
            for submission in subreddit.hot(limit=15):
                post_age_hours = (current_time - submission.created_utc) / 3600
                
                # Skip if post is too old or we already commented on it
                if post_age_hours > 6:  # 6 hours max for replies
                    continue
                    
                submission.comments.replace_more(limit=0)
                comments = submission.comments.list()
                
                # Find top-level comments with good engagement
                for comment in comments:
                    comment_age_hours = (current_time - comment.created_utc) / 3600
                    
                    # Criteria for replying to a comment:
                    # - Not too old (within 1 hour)
                    # - Has decent score (3+ upvotes)
                    # - Hasn't been replied to by us
                    # - Is a substantial comment (100+ chars)
                    # - Is making a judgment (contains NTA, YTA, etc.)
                    if (comment.id not in replied_comments and
                        comment_age_hours < 1 and  # Very fresh comments
                        comment.score >= 3 and
                        len(comment.body) > 100 and
                        any(judgment in comment.body.upper() for judgment in ['NTA', 'YTA', 'ESH', 'NAH'])):
                        
                        print(f"       [FOUND] Reply opportunity: Comment with {comment.score} upvotes")
                        return comment, submission
                        
        except Exception as e:
            print(f"       [ERROR] Error finding reply opportunities in r/{subreddit_name}: {e}")
            continue
            
    return None, None

def generate_comment_reply(chat_llm, original_comment, post_title, post_text):
    """Generate a reply to another comment"""
    try:
        reply_prompt = f"""
        Original Post Title: {post_title}
        Original Post: {post_text[:500]}...
        Comment to Reply To: {original_comment.body}
        
        Generate a thoughtful reply to this comment that:
        - Builds on their point naturally
        - Adds new insight or perspective  
        - Sounds conversational and authentic
        - Encourages further discussion
        - Shows you read and understood their comment
        - Is 1-2 sentences max for engagement
        
        Examples of good reply starters:
        - "This exactly!"
        - "So true, and also..."
        - "Yeah I was thinking the same thing about..."
        - "Adding to this..."
        - "100% agree, especially..."
        - "You nailed it, and the part about..."
        
        Generate a natural, engaging reply that feels authentic:
        """
        
        reply = chat_llm.llm.invoke(reply_prompt).content
        
        # Apply same human quirks to replies
        reply = chat_llm._add_human_quirks(reply)
        
        return reply.strip()
        
    except Exception as e:
        print(f"      [ERROR] Reply generation failed: {e}")
        return ""

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

def get_replied_comments(reddit):
    """Track comments we've already replied to"""
    print("[INFO] Loading previously replied-to comments...")
    replied_comments = set()
    try:
        for comment in reddit.user.me().comments.new(limit=1000):
            # If this comment is a reply to another comment (not a post)
            if hasattr(comment, 'parent_id') and comment.parent_id.startswith('t1_'):
                # Extract the parent comment ID
                parent_id = comment.parent_id[3:]  # Remove 't1_' prefix
                replied_comments.add(parent_id)
        print(f"       [SUCCESS] Found {len(replied_comments)} previously replied-to comments")
    except Exception as e:
        print(f"       [ERROR] Error retrieving replied comments: {e}")
    return replied_comments

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

def get_strategic_timing(action_type="comment"):
    """
    Calculate strategic timing based on Reddit engagement patterns
    Returns wait time in seconds
    """
    current_hour = datetime.now().hour
    
    # Peak hours on Reddit (EST): 8-10 AM, 12-2 PM, 6-10 PM
    peak_hours = [8, 9, 12, 13, 18, 19, 20, 21]
    
    base_wait = {
        "comment": (600, 1200),   # 10-20 minutes for comments
        "reply": (180, 600),      # 3-10 minutes for replies (faster engagement)
        "peak": (300, 900),       # 5-15 minutes during peak hours
        "off_peak": (900, 1800)   # 15-30 minutes during off-peak
    }
    
    # Adjust timing based on current hour
    if current_hour in peak_hours:
        # During peak hours, comment more frequently
        if action_type == "reply":
            wait_range = base_wait["reply"]
        else:
            wait_range = base_wait["peak"]
    else:
        # During off-peak, space out more
        wait_range = base_wait["off_peak"]
    
    # Add some randomness for human-like behavior
    wait_time = randint(wait_range[0], wait_range[1])
    
    # Add occasional longer breaks (10% chance)
    if random.random() < 0.1:
        wait_time += randint(300, 900)  # Add 5-15 minutes
        
    return wait_time

def add_realistic_delay(action_type="comment"):
    """Add realistic human-like delays before posting"""
    
    # Reading time: 10-45 seconds to "read" the post/comment
    reading_time = randint(10, 45)
    print(f"       [TIMING] Reading content... ({reading_time}s)")
    sleep(reading_time)
    
    # Thinking time: 15-60 seconds to "think" about response
    thinking_time = randint(15, 60)
    print(f"       [TIMING] Thinking about response... ({thinking_time}s)")
    sleep(thinking_time)
    
    # Typing time: Based on comment length simulation
    if action_type == "reply":
        typing_time = randint(30, 90)  # Replies are usually shorter
    else:
        typing_time = randint(60, 180)  # Comments are longer
    
    print(f"       [TIMING] Typing response... ({typing_time}s)")
    sleep(typing_time)
    
    # Final review time: 5-15 seconds to "review" before posting
    review_time = randint(5, 15)
    print(f"       [TIMING] Reviewing before posting... ({review_time}s)")
    sleep(review_time)

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
    
    # Load previously commented posts and replied comments
    commented_posts = get_commented_posts(reddit)
    replied_comments = get_replied_comments(reddit)
    
    print(f"\n[SYSTEM] Starting continuous search-comment-wait cycle...")
    print("="*50)
    
    cycle_count = 0
    daily_comment_count = 0
    daily_reply_count = 0
    max_daily_comments = 50  # Limit to 50 comments per day
    max_daily_replies = 20   # Limit to 20 replies per day
    
    with open("commented_post_links.txt", "a") as file:
        while True:  # Continuous loop
            cycle_count += 1
            print(f"\n[CYCLE {cycle_count}] Starting new search cycle...")
            print(f"[SYSTEM] Daily comments: {daily_comment_count}/{max_daily_comments}, replies: {daily_reply_count}/{max_daily_replies}")
            
            # Check daily limits
            if daily_comment_count >= max_daily_comments and daily_reply_count >= max_daily_replies:
                print(f"[SYSTEM] Daily limits reached. Sleeping for 12 hours...")
                sleep(12 * 60 * 60)  # Sleep for 12 hours
                daily_comment_count = 0  # Reset counters
                daily_reply_count = 0
                continue
            
            # Decide whether to post new comment or reply to existing one
            # 70% chance for new posts, 30% chance for replies (if under limits)
            action_choice = random.random()
            
            if (action_choice < 0.7 and daily_comment_count < max_daily_comments) or daily_reply_count >= max_daily_replies:
                # Search for a new post to comment on
                print(f"[CYCLE {cycle_count}] Looking for new post to comment on...")
                submission = find_single_post(reddit, commented_posts)
                
                if not submission:
                    print(f"[CYCLE {cycle_count}] No eligible posts found")
                else:
                    # Process new post comment (existing logic)
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
                        
                        # Add realistic human-like delay before posting
                        add_realistic_delay("comment")
                        
                        print(f"       [REDDIT] Posting comment...")
                        
                        # Post comment (existing logic)
                        comment_posted = False
                        while not comment_posted:
                            try:
                                response = submission.reply(comment)
                                file.write(f"{response.submission.url}\n")
                                file.flush()
                                comment_posted = True
                                daily_comment_count += 1
                                print(f"       [SUCCESS] Comment posted successfully!")
                                print(f"       [SYSTEM] Daily counts - Comments: {daily_comment_count}/{max_daily_comments}, Replies: {daily_reply_count}/{max_daily_replies}")
                                print(f"\n[POST DETAILS]")
                                print(f"Title: {submission.title}")
                                print(f"URL: {submission.url}")
                                print(f"Subreddit: r/{submission.subreddit}")
                                print(f"\n[COMMENT POSTED]")
                                print(f"{comment}")
                                print(f"\n" + "="*50)
                                
                                # Add to commented posts
                                commented_posts.add(submission.id)
                                
                            except RedditAPIException as e:
                                print(f"       [DEBUG] RedditAPIException details:")
                                print(f"       [DEBUG] Exception items: {e.items}")
                                
                                # Handle rate limiting (existing logic)
                                if any(item.error_type == "RATELIMIT" for item in e.items):
                                    rate_limit_item = next(item for item in e.items if item.error_type == "RATELIMIT")
                                    message = rate_limit_item.message
                                    try:
                                        words = message.split()
                                        if "minutes" in message:
                                            wait_minutes = int([w for w in words if w.isdigit()][-1])
                                        else:
                                            wait_minutes = 10
                                    except:
                                        wait_minutes = 10
                                    
                                    print(f"       [RATELIMIT] Hit rate limit: {message}")
                                    print(f"       [RATELIMIT] Waiting {wait_minutes} minutes...")
                                    sleep(wait_minutes * 60)
                                    sleep(300)  # Extra 5 minutes
                                    
                                elif any(item.error_type == "THREAD_LOCKED" for item in e.items):
                                    print(f"       [ERROR] Thread locked")
                                    comment_posted = True
                                else:
                                    error_types = [item.error_type for item in e.items]
                                    print(f"       [ERROR] Reddit API errors: {error_types}")
                                    comment_posted = True
                            except Exception as e:
                                print(f"       [ERROR] Unexpected error posting comment: {e}")
                                comment_posted = True
                    else:
                        print(f"       [ERROR] Failed to generate comment")
                        
            else:
                # Look for comments to reply to
                print(f"[CYCLE {cycle_count}] Looking for comments to reply to...")
                comment_to_reply, parent_submission = find_comments_to_reply_to(reddit, replied_comments)
                
                if not comment_to_reply:
                    print(f"[CYCLE {cycle_count}] No eligible comments found for replies")
                else:
                    print(f"\n[REPLY] Processing comment reply:")
                    print(f"        Original comment score: {comment_to_reply.score}")
                    print(f"        Comment length: {len(comment_to_reply.body)} chars")
                    print(f"        [AI] Generating reply...")
                    
                    reply = generate_comment_reply(generator_post, comment_to_reply, parent_submission.title, parent_submission.selftext)
                    
                    if reply:
                        print(f"        [AI] Generated reply ({len(reply)} chars)")
                        
                        # Add realistic human-like delay before posting reply
                        add_realistic_delay("reply")
                        
                        print(f"        [REDDIT] Posting reply...")
                        
                        # Post reply
                        reply_posted = False
                        while not reply_posted:
                            try:
                                response = comment_to_reply.reply(reply)
                                reply_posted = True
                                daily_reply_count += 1
                                print(f"        [SUCCESS] Reply posted successfully!")
                                print(f"        [SYSTEM] Daily counts - Comments: {daily_comment_count}/{max_daily_comments}, Replies: {daily_reply_count}/{max_daily_replies}")
                                print(f"\n[REPLY DETAILS]")
                                print(f"Original comment: {comment_to_reply.body[:100]}...")
                                print(f"Post: {parent_submission.title[:80]}...")
                                print(f"\n[REPLY POSTED]")
                                print(f"{reply}")
                                print(f"\n" + "="*50)
                                
                                # Add to replied comments
                                replied_comments.add(comment_to_reply.id)
                                
                            except RedditAPIException as e:
                                # Same error handling as comments
                                if any(item.error_type == "RATELIMIT" for item in e.items):
                                    rate_limit_item = next(item for item in e.items if item.error_type == "RATELIMIT")
                                    message = rate_limit_item.message
                                    try:
                                        words = message.split()
                                        if "minutes" in message:
                                            wait_minutes = int([w for w in words if w.isdigit()][-1])
                                        else:
                                            wait_minutes = 10
                                    except:
                                        wait_minutes = 10
                                    
                                    print(f"        [RATELIMIT] Hit rate limit: {message}")
                                    print(f"        [RATELIMIT] Waiting {wait_minutes} minutes...")
                                    sleep(wait_minutes * 60)
                                    sleep(300)
                                    
                                else:
                                    print(f"        [ERROR] Error posting reply: {e}")
                                    reply_posted = True
                            except Exception as e:
                                print(f"        [ERROR] Unexpected error posting reply: {e}")
                                reply_posted = True
                    else:
                        print(f"        [ERROR] Failed to generate reply")
            
            # Random chance to track comment performance
            if randint(1, 30) == 1:  # 3.3% chance
                pause_randomly()
                track_comment_performance(reddit, comment_storage)
            
            # Strategic timing based on Reddit engagement patterns
            last_action = "reply" if action_choice >= 0.7 else "comment"
            sleep_duration = get_strategic_timing(last_action)
            minutes = sleep_duration // 60
            seconds = sleep_duration % 60
            next_time = datetime.now() + timedelta(seconds=sleep_duration)
            
            current_hour = datetime.now().hour
            peak_indicator = "PEAK" if current_hour in [8, 9, 12, 13, 18, 19, 20, 21] else "off-peak"
            
            print(f"\n[WAIT] Strategic timing ({peak_indicator}): {minutes}m {seconds}s")
            print(f"       Next search at: {next_time.strftime('%H:%M:%S')}")
            
            sleep(sleep_duration)

if __name__ == "__main__":
    main()
