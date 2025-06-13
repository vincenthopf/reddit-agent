import config
import praw
from generator_comment import GeneratorCommentGPT

def test_reddit_connection():
    """Test Reddit API connection"""
    try:
        reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
            user_agent="Test Bot 1.0"
        )
        
        # Test connection by getting user info
        user = reddit.user.me()
        print(f"✅ Reddit connection successful! Logged in as: {user.name}")
        return True
        
    except Exception as e:
        print(f"❌ Reddit connection failed: {e}")
        return False

def test_openrouter_connection():
    """Test OpenRouter API connection"""
    try:
        generator = GeneratorCommentGPT(openrouter_api_key=config.OPENROUTER_API_KEY)
        
        # Test with a simple comment generation
        test_comment = generator.generate_comment(
            title="Test Post", 
            post_text="This is a test post to verify OpenRouter connection.", 
            comments=[]
        )
        
        if test_comment and len(test_comment.strip()) > 0:
            print("✅ OpenRouter connection successful!")
            print(f"   Sample response: {test_comment[:50]}...")
            return True
        else:
            print("❌ OpenRouter connection failed: Empty response")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter connection failed: {e}")
        return False

def main():
    print("Testing configuration...")
    print("=" * 40)
    
    # Check if all required environment variables are set
    required_vars = [
        'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 
        'REDDIT_USERNAME', 'REDDIT_PASSWORD', 
        'OPENROUTER_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(config, var, None)
        if not value:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return
    
    print("✅ All environment variables found")
    print()
    
    # Test connections
    reddit_ok = test_reddit_connection()
    print()
    openrouter_ok = test_openrouter_connection()
    print()
    
    if reddit_ok and openrouter_ok:
        print("🎉 All tests passed! Bot is ready to run.")
    else:
        print("⚠️  Some tests failed. Please check your configuration.")

if __name__ == "__main__":
    main()