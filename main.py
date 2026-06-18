import os
import json
import subprocess

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

load_dotenv()

# -------------------------
# LLM
# -------------------------

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

# -------------------------
# Current Repository
# -------------------------

CURRENT_REPO = None

# -------------------------
# Prompt
# -------------------------

SYSTEM_PROMPT = """
You are a Git Agent.

Convert user requests into JSON.

Return ONLY valid JSON.

Schema:

{
  "commands": []
}

Examples:

show branches

{
  "commands": ["git branch"]
}

show last commit

{
  "commands": ["git log -1"]
}

create branch feature-auth

{
  "commands": ["git checkout -b feature-auth"]
}

switch to main

{
  "commands": ["git checkout main"]
}

commit all changes as second commit

{
  "commands": [
    "git add .",
    "git commit -m \\"second commit\\""
  ]
}

push changes

{
  "commands": [
    "git push"
  ]
}

pull latest changes

{
  "commands": [
    "git pull"
  ]
}

merge feature-auth into main

{
  "commands": [
    "git checkout main",
    "git merge feature-auth"
  ]
}
"""

# -------------------------
# Safety
# -------------------------

BLOCKED = [
    "git reset --hard",
    "git clean -fd",
    "git push --force"
]


def is_safe(commands):

    for cmd in commands:

        for blocked in BLOCKED:

            if blocked in cmd:
                return False

    return True


# -------------------------
# Execute
# -------------------------

def execute(commands):

    global CURRENT_REPO

    outputs = []

    for cmd in commands:

        print(f"\nExecuting -> {cmd}")

        result = subprocess.run(
            cmd,
            cwd=CURRENT_REPO,
            shell=True,
            capture_output=True,
            text=True
        )

        output = ""

        if result.stdout:
            output += result.stdout

        if result.stderr:
            output += result.stderr

        outputs.append(output)

    return outputs


# -------------------------
# Open Repo
# -------------------------

def open_repo(path):

    global CURRENT_REPO

    git_dir = os.path.join(path, ".git")

    if not os.path.exists(git_dir):

        print("❌ Not a Git repository")

        return

    CURRENT_REPO = path

    print(f"\n✅ Repository Loaded")

    print(f"Path: {CURRENT_REPO}")


# -------------------------
# Clone Repo
# -------------------------

def clone_repo(url):

    folder = url.split("/")[-1]

    folder = folder.replace(".git", "")

    subprocess.run(
        f"git clone {url}",
        shell=True
    )

    path = os.path.abspath(folder)

    open_repo(path)


# -------------------------
# NLP Planner
# -------------------------

def create_plan(user_input):

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])

    return json.loads(response.content)


# -------------------------
# Main Loop
# -------------------------

print("\n===== Git Agent =====")

print("""
Commands:

open repo <path>

clone <github-url>

exit
""")

while True:

    query = input("\nGit Agent > ").strip()

    if query.lower() == "exit":
        break

    # ------------------
    # Open Local Repo
    # ------------------

    if query.startswith("open repo "):

        path = query.replace(
            "open repo ",
            ""
        ).strip()

        open_repo(path)

        continue

    # ------------------
    # Clone Repo
    # ------------------

    if query.startswith("clone "):

        url = query.replace(
            "clone ",
            ""
        ).strip()

        clone_repo(url)

        continue

    # ------------------
    # Repo Required
    # ------------------

    if not CURRENT_REPO:

        print(
            "Open a repository first."
        )

        continue

    try:

        plan = create_plan(query)

        commands = plan["commands"]

    except Exception as e:

        print(
            "Could not understand request."
        )

        print(e)

        continue

    if not is_safe(commands):

        print(
            "Blocked dangerous command."
        )

        continue

    outputs = execute(commands)

    print("\n===== RESULT =====")

    for output in outputs:

        print(output)