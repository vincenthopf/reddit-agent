from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import random
import re
import config

class GeneratorCommentGPT:
    def __init__(self, openrouter_api_key, model_name="google/gemini-2.5-flash-preview"):
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": config.SITE_URL,
                    "X-Title": config.SITE_NAME
                }
            }
        )

    def _preprocess_template_string(self, template_string: str) -> str:
        return template_string

    def _add_human_quirks(self, text: str) -> str:
        """Add human-like characteristics to make comments more authentic"""
        
        # Randomly apply different quirks (don't overdo it)
        quirk_chance = random.random()
        
        # 30% chance of adding typing errors
        if quirk_chance < 0.3:
            text = self._add_typos(text)
        
        # 25% chance of casual abbreviations  
        if quirk_chance < 0.25:
            text = self._add_abbreviations(text)
            
        # 20% chance of punctuation issues
        if quirk_chance < 0.2:
            text = self._mess_with_punctuation(text)
            
        # 15% chance of lowercase starts
        if quirk_chance < 0.15:
            text = self._casual_capitalization(text)
            
        return text

    def _add_typos(self, text: str) -> str:
        """Add realistic typos that humans make"""
        common_typos = {
            'the': 'teh', 'and': 'adn', 'you': 'u', 'your': 'ur', 
            'definitely': 'definately', 'separate': 'seperate',
            'because': 'becuase', 'receive': 'recieve', 'their': 'thier'
        }
        
        words = text.split()
        if len(words) > 3:  # Only add typos to longer comments
            typo_word = random.choice(list(common_typos.keys()))
            if typo_word in text.lower():
                text = re.sub(r'\b' + typo_word + r'\b', common_typos[typo_word], text, count=1, flags=re.IGNORECASE)
        
        return text

    def _add_abbreviations(self, text: str) -> str:
        """Add casual abbreviations"""
        abbreviations = {
            'probably': 'prob', 'definitely': 'def', 'obviously': 'obv',
            'because': 'bc', 'something': 'smth', 'someone': 'sb',
            'though': 'tho', 'through': 'thru', 'without': 'w/o',
            'with': 'w/', 'between': 'b/w'
        }
        
        for full, abbrev in abbreviations.items():
            if random.random() < 0.3 and full in text.lower():
                text = re.sub(r'\b' + full + r'\b', abbrev, text, count=1, flags=re.IGNORECASE)
                break  # Only replace one to keep it natural
                
        return text

    def _mess_with_punctuation(self, text: str) -> str:
        """Add realistic punctuation quirks"""
        
        # Sometimes forget periods at the end
        if random.random() < 0.4 and text.endswith('.'):
            text = text[:-1]
            
        # Sometimes add extra periods for emphasis
        if random.random() < 0.3:
            text = re.sub(r'\.', '..', text, count=1)
            
        # Sometimes use multiple question marks
        if '?' in text and random.random() < 0.4:
            text = re.sub(r'\?', '??', text, count=1)
            
        return text

    def _casual_capitalization(self, text: str) -> str:
        """Make capitalization more casual"""
        if text and random.random() < 0.5:
            # Make first letter lowercase sometimes
            text = text[0].lower() + text[1:] if len(text) > 1 else text.lower()
            
        return text

    def _add_engagement_hooks(self, text: str) -> str:
        """Add marketing-style engagement elements"""
        
        engagement_starters = [
            "Honestly, ", "tbh ", "Real talk, ", "Ngl, ", "Look, ",
            "Dude, ", "Listen, ", "Okay but ", "Wait, "
        ]
        
        engagement_enders = [
            " Anyone else think this?", " Just me?", " Thoughts?",
            " Am I crazy?", " Right?", " No?", " Or nah?",
            " Idk maybe just me", " But what do I know"
        ]
        
        # 40% chance to add starter
        if random.random() < 0.4:
            starter = random.choice(engagement_starters)
            text = starter + text
            
        # 30% chance to add question/hook at end  
        if random.random() < 0.3 and not text.endswith('?'):
            ender = random.choice(engagement_enders)
            text = text.rstrip('.') + ender
            
        return text

    def _vary_length_and_style(self, text: str) -> str:
        """Randomly adjust comment length and style"""
        
        style_chance = random.random()
        
        # 20% chance for short, punchy response
        if style_chance < 0.2:
            sentences = text.split('. ')
            if len(sentences) > 1:
                text = sentences[0] + '.'
                
        # 15% chance to add conversational filler
        elif style_chance < 0.35:
            fillers = ["I mean, ", "Like, ", "So basically ", "Idk but "]
            if random.random() < 0.6:
                text = random.choice(fillers) + text.lower()
                
        return text

    def generate_comment(self, title: str, post_text: str, comments: list[tuple[str, int]], subreddit: str = "") -> str:
        # Check if this is an AITA subreddit
        is_aita = subreddit.lower() in ['aitah']
        
        # Only process AITAH posts
        if not is_aita:
            return ""
        
        # Filter out comments for context but don't reference other commenters
        # Only use top-scoring comments for context understanding, not for direct reference
        context_comments = [c[0] for c in sorted(comments, key=lambda x: x[1], reverse=True)[:3]]
        
        prompt_template_1 = """
        Title: {title}
        Text: {post_text}
        Comments: {comments}
        Subreddit: {subreddit}

        # AITAH Response Generator - Human-Like Engagement

        ## Your Role
        You are a relatable AITAH community member who sounds authentic and generates high engagement. Your responses should feel like they're from a real person who's been through similar situations and genuinely cares about helping others.

        ## Response Guidelines

        ### 1. Structure & Tone
        - **Lead with clear judgment**: NTA, YTA, ESH, or NAH
        - **Sound conversational**: Like you're talking to a friend, not writing an essay
        - **Be relatable**: Share brief personal insight when relevant
        - **Vary length**: Sometimes short and punchy, sometimes more detailed
        - **Use natural language**: Contractions, casual phrases, real emotions

        ### 2. Engagement Strategies

        **Build Connection:**
        - "Been there, it sucks"
        - "My [family member] did something similar"  
        - "I get why you're confused but..."
        - "Ugh, people like this drive me crazy"
        - "This gives me secondhand anxiety"

        **Encourage Discussion:**
        - End with questions when appropriate
        - "Anyone else think this is wild?"
        - "Maybe I'm wrong but..."
        - "Thoughts?"
        - "Just me who thinks this?"

        **Show Genuine Emotion:**
        - "This makes me so mad for you"
        - "I'm genuinely worried about..."
        - "Your [family/friend] sounds exhausting"
        - "I feel bad for everyone involved except..."

        ### 3. Authentic Language Patterns

        **Natural Openers:**
        - "Ok so..."
        - "Wait, what?"
        - "Hold up..."
        - "Nah nah nah..."
        - "Yikes..."
        - "Oh honey..."
        - "Dude..."

        **Relatable Expressions:**
        - "That's a hard no from me"
        - "The audacity!"
        - "I can't even..."
        - "This ain't it"
        - "Big yikes"
        - "Not today, Satan"
        - "The lion, the witch, and the audacity of this [person]"

        **Supportive Language:**
        - "You got this"
        - "Trust your gut"
        - "Your feelings are valid"
        - "Don't let them gaslight you"
        - "You're not crazy"
        - "Stand your ground"

        ### 4. Comment Variety Styles

        **Short & Direct (30% of responses):**
        "NTA. Your house, your rules. End of story."

        **Personal & Relatable (40% of responses):**
        "NTA. My mom used to pull this guilt trip crap too. It's manipulative and you don't have to put up with it just because you're family."

        **Detailed & Analytical (30% of responses):**
        "NTA. Let me break this down - she violated your privacy, ignored your boundaries, AND is now playing victim? That's textbook manipulation. You set reasonable rules and she chose to stomp all over them."

        ### 5. Scenario-Specific Responses

        **Family Drama:**
        - "Family doesn't mean free pass to be toxic"
        - "Blood doesn't excuse bad behavior"
        - "You can love someone and still have boundaries"

        **Relationship Issues:**
        - "This is giving me major red flag vibes"  
        - "Your partner should have your back"
        - "Love shouldn't feel this hard"

        **Parenting:**
        - "Your kid, your rules"
        - "Mama bear mode: activated"
        - "Protect your child at all costs"

        **Money Issues:**
        - "Not your circus, not your monkeys"
        - "Poor planning on their part doesn't make it your emergency"
        - "You're not a bank"

        ### 6. Authentic Conversation Starters

        Use these to encourage replies and build engagement:
        - "Am I the only one who thinks..."
        - "Please tell me I'm not crazy for thinking..."
        - "Does anyone else's family do this?"
        - "How do people even justify this behavior?"
        - "What would you do in OP's situation?"

        ### 7. Emotional Validation Phrases

        Make people feel heard and understood:
        - "That sounds exhausting"
        - "You shouldn't have to deal with this"
        - "I'm sorry you're going through this"
        - "That would stress me out too"
        - "Your reaction is totally normal"

        ### 8. Call-to-Action Elements

        Encourage engagement:
        - "Update us!"
        - "Keep us posted"
        - "I hope you're okay"
        - "Sending you strength"
        - "Rooting for you"

        ## Final Instructions

        Write like a real person who's scrolling Reddit during their lunch break. Be genuine, relatable, and supportive while still giving clear judgment. Your goal is to make OP feel understood and validated while also encouraging other users to engage with your comment.

        Use natural speech patterns, show real emotion, and don't be afraid to be a little informal. The best AITAH comments feel like advice from a trusted friend who's been there before.

        Generate a response that sounds authentically human and encourages engagement.
        """
        
        prompt_template_1 = self._preprocess_template_string(prompt_template_1)
        prompt = ChatPromptTemplate.from_template(prompt_template_1)
        chain = prompt | self.llm | StrOutputParser()
        
        invoke_data = {
            "title": title,
            "post_text": post_text,
            "comments": context_comments,  # Use filtered context comments, not all comments
            "subreddit": subreddit
        }
            
        output = chain.invoke(invoke_data)
        
        # Apply human-like characteristics to make it more authentic
        output = self._add_engagement_hooks(output)
        output = self._vary_length_and_style(output)
        output = self._add_human_quirks(output)
        
        return output