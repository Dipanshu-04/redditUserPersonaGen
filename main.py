
"""
Reddit User Persona Generator

This script scrapes a Reddit user's profile and generates a detailed psychological
and behavioral persona based on their posting history.

Requirements:
    pip install requests beautifulsoup4 google-genai python-dotenv textstat

"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class RedditPost:
    """Data class for Reddit posts/comments"""
    content: str
    subreddit: str
    score: int
    timestamp: str
    post_type: str  # 'post' or 'comment'
    url: str
    title: str = ""

@dataclass
class UserPersona:
    """Data class for user persona"""
    username: str
    personality_traits: List[str]
    interests: List[str]
    communication_style: str
    activity_patterns: Dict[str, any]
    psychological_profile: Dict[str, str]
    citations: Dict[str, List[str]]

class RedditScraper:
    """Scrapes Reddit user profiles"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_user_data(self, username: str) -> List[RedditPost]:
        """
        Scrape user's posts and comments from their profile
        
        Args:
            username: Reddit username
            
        Returns:
            List of RedditPost objects
        """
        posts = []
        
        # Try both old and new Reddit URLs
        urls = [
            f"https://old.reddit.com/user/{username}",
            f"https://www.reddit.com/user/{username}"
        ]
        
        for base_url in urls:
            try:
                # Get posts
                posts.extend(self._scrape_posts(base_url, username))
                # Get comments  
                posts.extend(self._scrape_comments(base_url, username))
                
                if posts:  # If we got data from this URL, break
                    break
                    
            except Exception as e:
                print(f"Error scraping {base_url}: {e}")
                continue
                
        return posts
    
    def _scrape_posts(self, base_url: str, username: str) -> List[RedditPost]:
        """Scrape user's posts"""
        posts = []
        url = f"{base_url}/submitted"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse posts from old Reddit format
            for post_div in soup.find_all('div', class_='thing'):
                try:
                    title_elem = post_div.find('a', class_='title')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    post_url = title_elem.get('href', '')
                    
                    # Get subreddit
                    subreddit_elem = post_div.find('a', class_='subreddit')
                    subreddit = subreddit_elem.get_text(strip=True) if subreddit_elem else 'unknown'
                    
                    # Get score
                    score_elem = post_div.find('div', class_='score')
                    score = 0
                    if score_elem:
                        score_text = score_elem.get_text(strip=True)
                        try:
                            score = int(score_text) if score_text.isdigit() else 0
                        except:
                            score = 0
                    
                    # Get timestamp
                    time_elem = post_div.find('time')
                    timestamp = time_elem.get('datetime', '') if time_elem else ''
                    
                    # Get post content if available
                    content_elem = post_div.find('div', class_='usertext-body')
                    content = content_elem.get_text(strip=True) if content_elem else title
                    
                    posts.append(RedditPost(
                        content=content,
                        subreddit=subreddit,
                        score=score,
                        timestamp=timestamp,
                        post_type='post',
                        url=post_url,
                        title=title
                    ))
                    
                except Exception as e:
                    print(f"Error parsing post: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping posts: {e}")
            
        return posts
    
    def _scrape_comments(self, base_url: str, username: str) -> List[RedditPost]:
        """Scrape user's comments"""
        comments = []
        url = f"{base_url}/comments"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse comments from old Reddit format
            for comment_div in soup.find_all('div', class_='thing'):
                try:
                    # Get comment content
                    content_elem = comment_div.find('div', class_='usertext-body')
                    if not content_elem:
                        continue
                        
                    content = content_elem.get_text(strip=True)
                    
                    # Get subreddit
                    subreddit_elem = comment_div.find('a', class_='subreddit')
                    subreddit = subreddit_elem.get_text(strip=True) if subreddit_elem else 'unknown'
                    
                    # Get score
                    score_elem = comment_div.find('span', class_='score')
                    score = 0
                    if score_elem:
                        score_text = score_elem.get_text(strip=True)
                        try:
                            score = int(re.findall(r'\d+', score_text)[0]) if re.findall(r'\d+', score_text) else 0
                        except:
                            score = 0
                    
                    # Get timestamp
                    time_elem = comment_div.find('time')
                    timestamp = time_elem.get('datetime', '') if time_elem else ''
                    
                    # Get comment URL
                    permalink_elem = comment_div.find('a', class_='bylink')
                    comment_url = permalink_elem.get('href', '') if permalink_elem else ''
                    
                    comments.append(RedditPost(
                        content=content,
                        subreddit=subreddit,
                        score=score,
                        timestamp=timestamp,
                        post_type='comment',
                        url=comment_url,
                        title=""
                    ))
                    
                except Exception as e:
                    print(f"Error parsing comment: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping comments: {e}")
            
        return comments

class PersonaAnalyzer:
    """Analyzes Reddit data to create user personas"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            print("Warning: Gemini API key not found. Using basic analysis only.")
    
    #Analyze user's posts to create a persona
    def analyze_user(self, username: str, posts: List[RedditPost]) -> UserPersona:
        if not posts:
            return self._create_empty_persona(username)
            
        # Basic analysis
        activity_patterns = self._analyze_activity_patterns(posts)
        interests = self._analyze_interests(posts)
        
        # Advanced analysis using LLM if available
        if self.gemini_api_key:
            llm_analysis = self._llm_analyze_personality(posts)
            personality_traits = llm_analysis.get('personality_traits', [])
            communication_style = llm_analysis.get('communication_style', '')
            psychological_profile = llm_analysis.get('psychological_profile', {})
        else:
            personality_traits = self._basic_personality_analysis(posts)
            communication_style = self._analyze_communication_style(posts)
            psychological_profile = self._basic_psychological_profile(posts)
        
        # Generate citations
        citations = self._generate_citations(posts, personality_traits, interests)
        
        return UserPersona(
            username=username,
            personality_traits=personality_traits,
            interests=interests,
            communication_style=communication_style,
            activity_patterns=activity_patterns,
            psychological_profile=psychological_profile,
            citations=citations
        )
    
    def _analyze_activity_patterns(self, posts: List[RedditPost]) -> Dict[str, any]:
        """Analyze user's activity patterns"""
        if not posts:
            return {}
            
        subreddit_counts = {}
        post_count = 0
        comment_count = 0
        total_score = 0
        
        for post in posts:
            # Count by subreddit
            subreddit_counts[post.subreddit] = subreddit_counts.get(post.subreddit, 0) + 1
            
            # Count by type
            if post.post_type == 'post':
                post_count += 1
            else:
                comment_count += 1
                
            # Sum scores
            total_score += post.score
        
        # Most active subreddits
        top_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_posts': post_count,
            'total_comments': comment_count,
            'total_score': total_score,
            'average_score': total_score / len(posts) if posts else 0,
            'top_subreddits': top_subreddits,
            'subreddit_diversity': len(subreddit_counts)
        }
    
    def _analyze_interests(self, posts: List[RedditPost]) -> List[str]:
        """Analyze user's interests based on subreddits and content"""
        interests = []
        
        # Get interests from subreddits
        subreddit_counts = {}
        for post in posts:
            subreddit_counts[post.subreddit] = subreddit_counts.get(post.subreddit, 0) + 1
        
        # Top subreddits indicate interests
        top_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Map subreddits to interests
        subreddit_to_interest = {
            'gaming': 'Gaming',
            'games': 'Gaming',
            'technology': 'Technology',
            'programming': 'Programming',
            'python': 'Programming',
            'politics': 'Politics',
            'news': 'Current Events',
            'worldnews': 'Current Events',
            'science': 'Science',
            'askreddit': 'Social Discussion',
            'movies': 'Movies',
            'books': 'Reading',
            'music': 'Music',
            'food': 'Food',
            'cooking': 'Cooking',
            'fitness': 'Fitness',
            'sports': 'Sports',
            'travel': 'Travel',
            'photography': 'Photography',
            'art': 'Art',
            'history': 'History',
            'bitcoin': 'Cryptocurrency',
            'cryptocurrency': 'Cryptocurrency',
            'investing': 'Finance',
            'personalfinance': 'Finance',
            'relationship': 'Relationships',
            'dating': 'Dating',
            'parenting': 'Parenting'
        }
        
        for subreddit, count in top_subreddits:
            subreddit_lower = subreddit.lower()
            for key, interest in subreddit_to_interest.items():
                if key in subreddit_lower:
                    if interest not in interests:
                        interests.append(interest)
                    break
            else:
                # If no match, use subreddit name as interest
                if subreddit not in ['unknown', 'AskReddit'] and len(interests) < 15:
                    interests.append(subreddit.replace('r/', '').title())
        
        return interests[:10]  # Limit to top 10 interests
    
    def _basic_personality_analysis(self, posts: List[RedditPost]) -> List[str]:
        """Basic personality analysis without LLM"""
        traits = []
        
        if not posts:
            return traits
            
        # Analyze posting patterns
        total_posts = len(posts)
        total_score = sum(post.score for post in posts)
        avg_score = total_score / total_posts if total_posts > 0 else 0
        
        # Analyze content length
        avg_content_length = sum(len(post.content) for post in posts) / total_posts
        
        # Analyze subreddit diversity
        unique_subreddits = len(set(post.subreddit for post in posts))
        subreddit_diversity = unique_subreddits / total_posts if total_posts > 0 else 0
        
        # Infer traits
        if avg_score > 50:
            traits.append("Popular content creator")
        elif avg_score > 10:
            traits.append("Well-received contributor")
        
        if avg_content_length > 500:
            traits.append("Detailed communicator")
        elif avg_content_length > 100:
            traits.append("Thoughtful writer")
        else:
            traits.append("Concise communicator")
        
        if subreddit_diversity > 0.7:
            traits.append("Diverse interests")
        elif subreddit_diversity > 0.4:
            traits.append("Focused interests")
        else:
            traits.append("Specialized interests")
        
        # Analyze engagement patterns
        comment_ratio = sum(1 for post in posts if post.post_type == 'comment') / total_posts
        if comment_ratio > 0.8:
            traits.append("Active commenter")
        elif comment_ratio > 0.5:
            traits.append("Balanced contributor")
        else:
            traits.append("Content creator")
        
        return traits
    
    def _analyze_communication_style(self, posts: List[RedditPost]) -> str:
        """Analyze user's communication style"""
        if not posts:
            return "Unknown communication style"
        
        # Analyze text characteristics
        total_length = sum(len(post.content) for post in posts)
        avg_length = total_length / len(posts)
        
        # Count question marks and exclamation points
        questions = sum(post.content.count('?') for post in posts)
        exclamations = sum(post.content.count('!') for post in posts)
        
        # Analyze capitalization
        all_caps_posts = sum(1 for post in posts if post.content.isupper() and len(post.content) > 10)
        caps_ratio = all_caps_posts / len(posts)
        
        # Determine style
        if avg_length > 500:
            style = "Detailed and thorough"
        elif avg_length > 100:
            style = "Moderate length posts"
        else:
            style = "Brief and concise"
        
        if questions > len(posts) * 0.3:
            style += ", inquisitive"
        
        if exclamations > len(posts) * 0.2:
            style += ", enthusiastic"
        
        if caps_ratio > 0.1:
            style += ", emphatic"
        
        return style
    
    def _basic_psychological_profile(self, posts: List[RedditPost]) -> Dict[str, str]:
        """Basic psychological profiling without LLM"""
        profile = {}
        
        if not posts:
            return profile
        
        # Analyze engagement level
        total_posts = len(posts)
        avg_score = sum(post.score for post in posts) / total_posts
        
        if total_posts > 100:
            profile['Activity Level'] = 'Highly active'
        elif total_posts > 20:
            profile['Activity Level'] = 'Moderately active'
        else:
            profile['Activity Level'] = 'Casual user'
        
        # Analyze social validation seeking
        if avg_score > 100:
            profile['Social Validation'] = 'High engagement seeker'
        elif avg_score > 10:
            profile['Social Validation'] = 'Moderate engagement seeker'
        else:
            profile['Social Validation'] = 'Low engagement seeker'
        
        # Analyze content diversity
        unique_subreddits = len(set(post.subreddit for post in posts))
        if unique_subreddits > 20:
            profile['Interest Breadth'] = 'Very diverse interests'
        elif unique_subreddits > 5:
            profile['Interest Breadth'] = 'Diverse interests'
        else:
            profile['Interest Breadth'] = 'Focused interests'
        
        return profile
    
    def _llm_analyze_personality(self, posts: List[RedditPost]) -> Dict[str, any]:
        """Use LLM to analyze personality (requires Gemini API key)"""
        if not self.gemini_api_key or not posts:
            return {}
        
        # Prepare sample content for analysis
        sample_content = []
        for post in posts[:20]:  # Limit to avoid token limits
            sample_content.append(f"[{post.post_type}] {post.content[:200]}...")
        
        content_text = "\n".join(sample_content)
        
        prompt = f"""
        Analyze the following Reddit posts and comments to create a psychological profile:

        {content_text}

        Please provide your analysis in the following JSON format:
        {{
            "personality_traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
            "communication_style": "brief description of communication style",
            "psychological_profile": {{
                "Social Orientation": "description",
                "Emotional Pattern": "description",
                "Thinking Style": "description",
                "Behavior Pattern": "description"
            }}
        }}

        Focus on:
        1. Personality traits (5-7 specific traits based on posting patterns)
        2. Communication style (how they express themselves)
        3. Psychological characteristics (social, emotional, cognitive patterns)

        Respond with ONLY the JSON object, no additional text.
        """
        
        try:
            from google import genai
            
            client = genai.Client()
            
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            
            # Check if response and content exist
            if not response or not response.text:
                print("Error: Empty response from Gemini API")
                return {}
            
            result = response.text.strip()
            
            # Check if result is not None or empty
            if not result:
                print("Error: Empty content from Gemini API")
                return {}
            # Clean up the response - remove any markdown formatting
            if result.startswith('```json'):
                result = result[7:]  # Remove ```json
            if result.endswith('```'):
                result = result[:-3]  # Remove ```
            result = result.strip()

            # Try to parse JSON
            try:
                parsed_result = json.loads(result)
                
                # Validate the structure
                if not isinstance(parsed_result, dict):
                    raise ValueError("Response is not a dictionary")
                
                # Ensure required keys exist
                if 'personality_traits' not in parsed_result:
                    parsed_result['personality_traits'] = ['Unable to determine from AI response']
                if 'communication_style' not in parsed_result:
                    parsed_result['communication_style'] = 'Unable to determine from AI response'
                if 'psychological_profile' not in parsed_result:
                    parsed_result['psychological_profile'] = {'Status': 'Unable to determine from AI response'}
                
                return parsed_result
                
            except (json.JSONDecodeError, ValueError) as json_error:
                print(f"Error parsing JSON from Gemini response: {json_error}")
                print(f"Raw response: {result}")
                # Return fallback structure
                return {
                    'personality_traits': ['Unable to parse AI response'],
                    'communication_style': 'Unable to parse AI response',
                    'psychological_profile': {'Status': 'AI parsing failed'}
                }
            
        except ImportError:
            print("Error: google-genai library not installed. Run: pip install google-genai")
            return {}
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return {}
    
    def _generate_citations(self, posts: List[RedditPost], traits: List[str], interests: List[str]) -> Dict[str, List[str]]:
        """Generate citations for personality traits and interests"""
        citations = {}
        
        # Cite posts for interests
        for interest in interests:
            citations[f"Interest: {interest}"] = []
            for post in posts:
                if interest.lower() in post.subreddit.lower() or interest.lower() in post.content.lower():
                    citation = f"[{post.post_type}] in r/{post.subreddit}: \"{post.content[:100]}...\""
                    citations[f"Interest: {interest}"].append(citation)
                    if len(citations[f"Interest: {interest}"]) >= 3:  # Limit citations
                        break
        
        # Cite posts for traits (simplified)
        for trait in traits:
            citations[f"Trait: {trait}"] = []
            # Add sample posts as evidence
            for post in posts[:3]:  # Use first few posts as general evidence
                citation = f"[{post.post_type}] in r/{post.subreddit}: \"{post.content[:100]}...\""
                citations[f"Trait: {trait}"].append(citation)
        
        return citations
    
    def _create_empty_persona(self, username: str) -> UserPersona:
        """Create empty persona when no data is available"""
        return UserPersona(
            username=username,
            personality_traits=["Unable to determine - no data available"],
            interests=["Unable to determine - no data available"],
            communication_style="Unable to determine - no data available",
            activity_patterns={},
            psychological_profile={"Status": "No data available"},
            citations={}
        )

class PersonaReporter:
    """Generates reports from user personas"""
    
    def generate_report(self, persona: UserPersona) -> str:
        """Generate a comprehensive text report"""
        report = []
        report.append("=" * 80)
        report.append(f"REDDIT USER PERSONA REPORT: u/{persona.username}")
        report.append("=" * 80)
        report.append("")
        
        # Activity Overview
        report.append("ACTIVITY OVERVIEW")
        report.append("-" * 40)
        if persona.activity_patterns:
            report.append(f"Total Posts: {persona.activity_patterns.get('total_posts', 0)}")
            report.append(f"Total Comments: {persona.activity_patterns.get('total_comments', 0)}")
            report.append(f"Average Score: {persona.activity_patterns.get('average_score', 0):.1f}")
            report.append(f"Subreddit Diversity: {persona.activity_patterns.get('subreddit_diversity', 0)}")
            
            if persona.activity_patterns.get('top_subreddits'):
                report.append("\nTop Subreddits:")
                for subreddit, count in persona.activity_patterns['top_subreddits'][:5]:
                    report.append(f"  • r/{subreddit}: {count} posts")
        else:
            report.append("No activity data available")
        
        report.append("")
        
        # Personality Traits
        report.append("PERSONALITY TRAITS")
        report.append("-" * 40)
        for trait in persona.personality_traits:
            report.append(f"• {trait}")
        report.append("")
        
        # Interests
        report.append("INTERESTS")
        report.append("-" * 40)
        for interest in persona.interests:
            report.append(f"• {interest}")
        report.append("")
        
        # Communication Style
        report.append("COMMUNICATION STYLE")
        report.append("-" * 40)
        report.append(persona.communication_style)
        report.append("")
        
        # Psychological Profile
        report.append("PSYCHOLOGICAL PROFILE")
        report.append("-" * 40)
        for key, value in persona.psychological_profile.items():
            report.append(f"{key}: {value}")
        report.append("")
        
        # Citations
        report.append("CITATIONS & EVIDENCE")
        report.append("-" * 40)
        for category, citations in persona.citations.items():
            if citations:
                report.append(f"\n{category}:")
                for citation in citations[:3]:  # Limit to 3 citations per category
                    report.append(f"  • {citation}")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, persona: UserPersona, filename: Optional[str] = None):
        """Save report to file"""
        if not filename:
            filename = f"persona_{persona.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report = self.generate_report(persona)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Report saved to: {filename}")
        return filename

def extract_username_from_url(url: str) -> str:
    """Extract username from Reddit URL"""
    # Handle various Reddit URL formats
    patterns = [
        r'reddit\.com/user/([^/]+)',
        r'reddit\.com/u/([^/]+)',
        r'old\.reddit\.com/user/([^/]+)',
        r'old\.reddit\.com/u/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it is already an username
    return url.strip('/')

def main():
    """Main function"""
    print("Reddit User Persona Generator")
    print("=" * 50)
    
    # Get user input
    user_input = input("Enter Reddit user URL or username: ").strip()
    
    if not user_input:
        print("Error: Please provide a Reddit user URL or username")
        return
    
    # Extract username
    username = extract_username_from_url(user_input)
    print(f"Analyzing user: u/{username}")
    
    # Initialize components
    scraper = RedditScraper()
    analyzer = PersonaAnalyzer()
    reporter = PersonaReporter()
    
    try:
        # Scrape user data
        print("Scraping user data...")
        posts = scraper.get_user_data(username)
        
        if not posts:
            print("Warning: No posts found. The user may not exist, be private, or have no public posts.")
            print("Creating empty persona...")
        else:
            print(f"Found {len(posts)} posts/comments")
        
        # Analyze user
        print("Analyzing user persona...")
        persona = analyzer.analyze_user(username, posts)
        
        # Generate and save report
        print("Generating report...")
        filename = reporter.save_report(persona)
        
        # Display summary
        print("\n" + "=" * 50)
        print("PERSONA SUMMARY")
        print("=" * 50)
        print(f"Username: u/{username}")
        print(f"Personality Traits: {', '.join(persona.personality_traits[:3])}...")
        print(f"Top Interests: {', '.join(persona.interests[:3])}...")
        print(f"Communication Style: {persona.communication_style}")
        print(f"\nFull report saved to: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please check the username and try again.")

if __name__ == "__main__":
    main()