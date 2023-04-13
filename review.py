import os
import requests
import json
import openai


def get_review():
    ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
    GIT_COMMIT_HASH = os.getenv("GIT_COMMIT_HASH")
    PR_PATCH_URL = os.getenv("GIT_PATCH_OUTPUT")
    model = "gpt-4-0314"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.organization = os.getenv("OPENAI_ORG_KEY")
    pr_link = os.getenv("LINK")

    headers = {
        "Accept": "application/vnd.github.v3.patch",
        "authorization": f"Bearer {ACCESS_TOKEN}",
    }
    
    # Fetch the patch file content
    patch_response = requests.get(PR_PATCH_URL, headers=headers)
    PR_PATCH = patch_response.text
    
    patch_info = f"Is there a better way to write this code? \n\n{PR_PATCH}\n"    

    print(f"\nPrompt sent to GPT-4: {patch_info}\n")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": patch_info},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.4,
        max_tokens=312,
        top_p=1,
        frequency_penalty=0.3,
        presence_penalty=0.6,
    )
    review = response["choices"][0]["message"]["content"]

    data = {"body": review, "commit_id": GIT_COMMIT_HASH, "event": "COMMENT"}
    data = json.dumps(data)
    print(f"\nResponse from GPT-4: {data}\n")

    OWNER = pr_link.split("/")[-4]
    REPO = pr_link.split("/")[-3]
    PR_NUMBER = pr_link.split("/")[-1]

    # https://api.github.com/repos/OWNER/REPO/pulls/PULL_NUMBER/reviews
    response = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/reviews",
        headers=headers,
        data=data,
    )
    print(response.json())


if __name__ == "__main__":
    get_review()
