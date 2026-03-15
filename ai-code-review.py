#import the OpenAI package so the script can catch OpenAI-specific errors
import openai

#import the OpenAI client class used to send the request
from openai import OpenAI

#import os so the script can read environment variables
import os


#read the pull request diff that the GitHub Actions workflow created
with open("diff.txt", "r") as file:
    diff = file.read()


#create the OpenAI client using the API key stored in the environment
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


#read the model name from the environment, or use the required default model
model_name = os.getenv("OPENAI_MODEL", "gpt-5.1-codex-mini")


#try to send the diff to the model and get review feedback back
try:
    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": "You are an expert software engineer performing who is going to be preforming a software code review on a Django app/project. Please prorovide thoughtful and helpful feedback on the code about what is good and what is not.",
            },
            {
                "role": "user",
                "content": f"Provide clear and concise feedback in the Markdown format. Please keep a close on Django convention, security, and code efficiency and report on changes for each one. In each case that you do so, please try and mention the file name and line number when possible as to help users better understand exactly what some feedback is referring to. Now here is the pull request file for you to read called diff: \n{diff}",
            },
        ],
    )

    #save the model response into the feedback variable
    feedback = response.output_text

    #print the feedback into the GitHub Actions log
    print(feedback)


#handle the case where the API usage limit has been reached
except openai.RateLimitError:
    print("Quota exceeded")
    feedback = "***Quota Exceeded***\nNo AI review available."


#handle any other unexpected error so the workflow still creates feedback.md
except Exception as error:
    print(f"Error: {error}")
    feedback = f"***Review Failed***\n{error}"


#remove the opening markdown code fence if the model included one
if feedback.startswith("```markdown"):
    feedback = feedback[len("```markdown"):]
elif feedback.startswith("```"):
    feedback = feedback[len("```"):]


#remove the closing markdown code fence if the model included one
feedback_stripped = feedback.rstrip()
if feedback_stripped.endswith("```"):
    feedback = feedback[:len(feedback) - 3]


#write the final review into the markdown file that the workflow will upload and post
with open("feedback.md", "w") as file:
    file.write(f"## AI Code Review Feedback\n\n{feedback}")
