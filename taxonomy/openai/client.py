"""openai client"""

import litellm

from django.conf import settings

litellm.api_key = settings.OPENAI_API_KEY


def chat_completion(prompt):
    """
    Use chatGPT https://api.openai.com/v1/chat/completions endpoint to generate a response.

    Arguments:
        prompt (str): chatGPT prompt
    """
    response = litellm.completion(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
    )

    content = response['choices'][0]['message']['content']
    return content
