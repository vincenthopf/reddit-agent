import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class CommentStorage:
    def __init__(self, storage_file: str = "stored_comments.json"):
        self.storage_file = storage_file
        self.comments = self._load_comments()
    
    def _load_comments(self) -> Dict:
        """Load stored comments from JSON file"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"comments": [], "stats": {"total_stored": 0, "downvoted": 0, "underperforming": 0}}
    
    def _save_comments(self):
        """Save comments to JSON file"""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.comments, f, indent=2, ensure_ascii=False)
    
    def store_comment(self, comment_id: str, comment_body: str, score: int, 
                     post_url: str, post_title: str, subreddit: str, 
                     reason: str, age_hours: float):
        """Store a comment with its metadata"""
        comment_data = {
            "id": comment_id,
            "body": comment_body,
            "score": score,
            "post_url": post_url,
            "post_title": post_title,
            "subreddit": subreddit,
            "reason": reason,
            "age_hours": age_hours,
            "stored_at": datetime.now().isoformat(),
            "stored_timestamp": time.time()
        }
        
        self.comments["comments"].append(comment_data)
        self.comments["stats"]["total_stored"] += 1
        
        if reason == "downvoted":
            self.comments["stats"]["downvoted"] += 1
        elif reason == "underperforming":
            self.comments["stats"]["underperforming"] += 1
        
        self._save_comments()
        
        return comment_data
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        return self.comments["stats"]
    
    def get_comments_by_reason(self, reason: str) -> List[Dict]:
        """Get comments filtered by storage reason"""
        return [c for c in self.comments["comments"] if c["reason"] == reason]
    
    def get_comments_by_subreddit(self, subreddit: str) -> List[Dict]:
        """Get comments filtered by subreddit"""
        return [c for c in self.comments["comments"] if c["subreddit"].lower() == subreddit.lower()]
    
    def search_comments(self, query: str) -> List[Dict]:
        """Search comments by content"""
        query_lower = query.lower()
        return [c for c in self.comments["comments"] 
                if query_lower in c["body"].lower() or query_lower in c["post_title"].lower()]