import os
import requests
import json
import openai

def get_review():
    ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
    GIT_COMMIT_HASH = os.getenv("GIT_COMMIT_HASH")
    model = "gpt-4"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.organization = os.getenv("OPENAI_ORG_KEY")
    pr_link = os.getenv("LINK")

    headers = {
        "Accept": "application/vnd.github.v3.patch",
        "authorization": f"Bearer {ACCESS_TOKEN}",
    }
    
    OWNER = pr_link.split("/")[-4]
    REPO = pr_link.split("/")[-3]
    PR_NUMBER = pr_link.split("/")[-1]

    # Get the patch of the pull request
    pr_details_url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}"
    pr_details_response = requests.get(pr_details_url, headers=headers)
    if pr_details_response.status_code != 200:
        print(f"Error fetching pull request details: {pr_details_response.status_code} - {pr_details_response.text}")
        return
    
    complete_prompt = '''    
    Act as a code reviewer of a Pull Request, providing feedback on the code changes below. You are provided with the Pull Request changes in a patch format.
    Each patch entry has the commit message in the Subject line followed by the code changes (diffs) in a unidiff format.    
    The above format for changes consists of multiple patches of code changes. 
    Each patch contains the files and the lines that were removed and the lines that were added. 
    Take into account that the lines that were removed or added may not be contiguous.
    The last patch might modify previously modified lines, so take always the last patch where a line was modified
    as the final version of the line.
    Important instructions:
    - Your task is to do a line by line review of new hunks and point out 
      substantive issues in those line ranges. For each issue you 
      identify, please provide the exact line range (inclusive) where 
      the issue occurs.
    - Only respond in the below response format (consisting of review
      sections) and nothing else. Each review section must consist of a line 
      range and a review comment for that line range. Optionally, 
      you can include a single replacement suggestion snippet and/or multiple 
      new code snippets in the review comment. There's a separator between review 
      sections.
    - Use Markdown format for review comment text.
    - Fenced code blocks must be used for new content and replacement 
      code/text snippets.  
    - Replacement code/text snippets must be complete and correctly 
      formatted. Each replacement suggestion must be provided as a separate review 
      section with relevant line number ranges.  
    - If needed, suggest new code using the correct language identifier in the 
      fenced code blocks. These snippets may be added to a different file, such 
      as test cases. Multiple new code snippets are allowed within a single 
      review section.
    - Do not annotate code snippets with line numbers inside the code blocks.
    - If there are no substantive issues detected at a line range, simply 
      comment "LGTM!" for the respective line range in a review section and 
      avoid additional commentary/compliments.
    - Review your comments and line ranges at least 3 times before sending 
      the final response to ensure accuracy of line ranges and replacement
      snippets.
    Response format expected:
      <start_line_number>-<end_line_number>:
      <review comment>
      ---
      <start_line_number>-<end_line_number>:
      <review comment>
      \`\`\`suggestion
      <code/text that replaces everything between start_line_number and end_line_number>
      \`\`\`
      ---
      <start_line_number>-<end_line_number>:
      <review comment>
      \`\`\`<language>
      <new code snippet>
      \`\`\`
      ---
      ...
    Example changes:
      ---new_hunk---
      1: def add(x, y):
      2:     z = x+y
      3:     retrn z
      4:
      5: def multiply(x, y):
      6:     return x * y
      
      ---old_hunk---
      def add(x, y):
          return x + y
    Example response:
      3-3:
      There's a typo in the return statement.
      \`\`\`suggestion
          return z
      \`\`\`
      ---
      5-6:
      LGTM!
      ---
    The patch or patches for review are below:    
    '''
    prompt = complete_prompt + pr_details_response.text

    print(f"\nPrompt sent to GPT-4: {prompt}\n")
    
    messages = [
        {"role": "system", "content": "You are an experienced software developer."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=312,
            top_p=1,
            frequency_penalty=0.3,
            presence_penalty=0.6,
        )
    except openai.error.RateLimitError as e:
        print(f"RateLimitError: {e}")
        print("You have exceeded your current quota. Please check your plan and billing details.")
        return
        
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
