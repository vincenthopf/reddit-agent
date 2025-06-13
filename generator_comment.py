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

    def generate_comment(self, title: str, post_text: str, comments: list[tuple[str, int]]) -> str:
        prompt_template_1 = """
        Title: {title}
        Text: {post_text}
        Comments: {comments}

        This appears to be a moral judgment post (AITAH, relationship advice, etc.). Provide a thoughtful, balanced response:

        1. Read the situation carefully and consider multiple perspectives
        2. Make a moral judgment if appropriate (NTA, YTA, ESH, NAH for AITAH posts)
        3. Provide reasoning for your judgment based on the specific details
        4. Be empathetic but honest in your assessment
        5. Offer constructive advice when relevant
        6. Consider the consequences and broader context of the situation

        Guidelines:
        - Be respectful and thoughtful, not judgmental or harsh
        - Focus on actions and behaviors, not character assassination
        - Acknowledge when situations are complex or nuanced
        - Use empathetic language while being direct about problematic behavior
        - Keep your response concise but substantive (20-50 words)

        Your goal is to provide a helpful, morally-grounded comment that adds value to the discussion.
        """
        
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
        - Include relevant acronyms (NTA/YTA/etc.) for AITAH posts
        - 25-60 words maximum

        Focus on being genuinely helpful while respecting the complexity of human relationships.
        """
        
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
        output = chain.invoke({
            "title": title,
            "post_text": post_text,
            "comments": comments
        })
        return output