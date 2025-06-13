from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import random
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

    def generate_comment(self, title: str, post_text: str, comments: list[tuple[str, int]], subreddit: str = "") -> str:
        # Check if this is an AITA subreddit
        is_aita = subreddit.lower() in ['aitah', 'amitheasshole']
        
        if is_aita:
            prompt_template_1 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}
            Subreddit: {subreddit}

            This is an AITA/AITAH post requiring a judgment. You MUST start your response with one of these judgments:
            - NTA (Not The Asshole)
            - YTA (You're The Asshole) 
            - ESH (Everyone Sucks Here)
            - NAH (No Assholes Here)

            Format: Start with the judgment, then provide reasoning.
            Example: "NTA. Your feelings are completely valid here..."

            Guidelines:
            1. ALWAYS start with the judgment acronym
            2. Provide clear reasoning based on the specific situation
            3. Be empathetic but honest in your assessment
            4. Focus on actions and behaviors, not character
            5. Keep response concise but substantive (20-50 words)

            Your goal is to provide a helpful AITA judgment that follows subreddit rules.
            """
        else:
            prompt_template_1 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}

            This appears to be a moral judgment post (relationship advice, confession, etc.). Provide a thoughtful, balanced response:

            1. Read the situation carefully and consider multiple perspectives
            2. Provide reasoning based on the specific details
            3. Be empathetic but honest in your assessment
            4. Offer constructive advice when relevant
            5. Consider the consequences and broader context of the situation

            Guidelines:
            - Be respectful and thoughtful, not judgmental or harsh
            - Focus on actions and behaviors, not character assassination
            - Acknowledge when situations are complex or nuanced
            - Use empathetic language while being direct about problematic behavior
            - Keep your response concise but substantive (20-50 words)

            Your goal is to provide a helpful, morally-grounded comment that adds value to the discussion.
            """
        
        if is_aita:
            prompt_template_2 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}
            Subreddit: {subreddit}

            This is an AITA/AITAH post requiring a judgment. You MUST start with NTA, YTA, ESH, or NAH.

            For this relationship/moral dilemma, provide supportive guidance:

            1. **Start with judgment** (NTA/YTA/ESH/NAH)
            2. **Validate feelings** where appropriate
            3. **Identify concerning behaviors** if present
            4. **Suggest communication strategies** for relationship issues
            5. **Encourage healthy boundaries** when needed

            Response style:
            - ALWAYS begin with judgment acronym
            - Warm but direct tone
            - Evidence-based reasoning from post details
            - 25-60 words maximum

            Example: "NTA. Your boundaries are important and..."
            """
        else:
            prompt_template_2 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}

            For this relationship/moral dilemma post, provide supportive guidance:

            1. **Validate feelings** where appropriate - acknowledge the poster's emotions
            2. **Identify red flags** or concerning behaviors if present
            3. **Suggest communication strategies** for relationship issues
            4. **Encourage healthy boundaries** when needed
            5. **Offer practical next steps** or resources if relevant
            6. **Be trauma-informed** and sensitive to difficult situations

            Response style:
            - Warm but direct tone
            - Evidence-based reasoning from the post details
            - Avoid being preachy or overly dramatic
            - 25-60 words maximum

            Focus on being genuinely helpful while respecting the complexity of human relationships.
            """
        
        if is_aita:
            prompt_template_3 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}
            Subreddit: {subreddit}

            This is an AITA/AITAH post requiring a judgment. You MUST start with NTA, YTA, ESH, or NAH.

            For this confession/advice post, respond with wisdom and perspective:

            1. **Start with judgment** (NTA/YTA/ESH/NAH)
            2. **Show understanding** without condoning harmful actions
            3. **Provide moral clarity** on right vs wrong behavior
            4. **Suggest accountability steps** if someone caused harm
            5. **Offer hope and growth mindset** for positive change

            Tone guidelines:
            - ALWAYS begin with judgment acronym
            - Compassionate but honest
            - Constructive and forward-looking
            - 20-50 words

            Example: "YTA. While I understand your frustration..."
            """
        else:
            prompt_template_3 = """
            Title: {title}
            Text: {post_text}
            Comments: {comments}

            For this confession/advice post, respond with wisdom and perspective:

            1. **Show understanding** without condoning harmful actions
            2. **Provide moral clarity** on right vs wrong behavior
            3. **Suggest accountability steps** if someone caused harm
            4. **Offer hope and growth mindset** for positive change
            5. **Share relevant insights** about human nature or relationships
            6. **Encourage professional help** when situations are serious

            Tone guidelines:
            - Compassionate but honest
            - Non-judgmental about the person, clear about actions
            - Constructive and forward-looking
            - Grounded in common sense and ethics
            - 20-50 words

            Aim to be the voice of wisdom someone needs to hear - caring but truthful.
            """
        
        prompt_template_1 = self._preprocess_template_string(prompt_template_1)
        prompt_template_2 = self._preprocess_template_string(prompt_template_2)
        prompt_template_3 = self._preprocess_template_string(prompt_template_3)
        selected_prompt_template = random.choice([prompt_template_1, prompt_template_2, prompt_template_3])
        prompt = ChatPromptTemplate.from_template(selected_prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        invoke_data = {
            "title": title,
            "post_text": post_text,
            "comments": comments
        }
        
        # Add subreddit to invoke data for AITA posts
        if is_aita:
            invoke_data["subreddit"] = subreddit
            
        output = chain.invoke(invoke_data)
        return output