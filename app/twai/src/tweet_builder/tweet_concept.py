import os
import shutil
import json
import random
import logging
import openai

logger = logging.getLogger("tweet")

IDEA_BANK = "idea_bank"
USED_IDEAS = "used_ideas"
MODEL_NAME = "gpt-3.5-turbo"

def check_tweet_length(tweet, max_length):
    if len(tweet) > max_length:
        return False
    return True


def generate_shorter_tweet(conversation_history):
    conversation_history.append({
        "role": "user",
        "content": "The tweet is too long. Please generate a shorter tweet, making it sound more natural and less buzzword-heavy. Feel free to drop emojis or hashtags if needed."
    })
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=conversation_history
    ).choices[0].message
    conversation_history.append(response)
    return response, conversation_history


def fetch_idea():
    '''
    Retrieve an idea from the idea bank if available.
    '''
    ideas = os.listdir(IDEA_BANK)
    if not ideas:
        return None
    idea = random.choice(ideas)
    with open(f"./{IDEA_BANK}/{idea}", "r", encoding="utf-8") as idea_file:
        idea_content = idea_file.read()
    os.makedirs(USED_IDEAS, exist_ok=True)
    shutil.move(f"{IDEA_BANK}/{idea}", f"{USED_IDEAS}/{idea}")
    return idea_content


def generate_concept(promp, OPEN_AI_KEY):
    '''
    Generate the concept for the tweet.
    '''
    openai.api_key = OPEN_AI_KEY
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, 'prompts', 'concept_system.txt')
    with open(file_path, "r", encoding="utf-8") as prompt_file:
        system_prompt = prompt_file.read().replace("{{prompt}}", promp)
    initial_idea = fetch_idea()
    user_content = promp if promp is not None else f"I have an idea for a tweet. {initial_idea}"
    conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    final_concept = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=conversation_history,
        temperature=1.2
    ).choices[0].message
    conversation_history.append(final_concept)
    if not check_tweet_length(final_concept.content, 280):
        final_tweet, _ = generate_shorter_tweet(conversation_history)
    return final_concept.content.strip(), conversation_history


if __name__ == "__main__":
    concept, message_history = generate_concept()
    print(concept)
    print(json.dumps(message_history, indent=4, sort_keys=True))
