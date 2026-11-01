# AGENT CITY local relay tools

These scripts are independent of the older working \`chrome_relay.py\` and \`relay.py\`. They are designed for Python 3.12 on macOS with Chrome and authenticated GitHub CLI.

The source is public, but **private ChatGPT conversation URLs and watcher state stay only on the local Mac**. Do not commit \`tabs.local.json\` or any personal conversation URLs.

## 1. Download scripts into the existing local project

Run in Terminal:

\`\`\`sh
cd ~/Downloads/agent_city_relay
curl -fsSL https://raw.githubusercontent.com/kuke2013-hub/agents/main/automation/chrome_tabs.py -o chrome_tabs.py
curl -fsSL https://raw.githubusercontent.com/kuke2013-hub/agents/main/automation/github_watch.py -o github_watch.py
python3.12 -m py_compile chrome_tabs.py github_watch.py
\`\`\`

No other Python packages are required. These tools do not call the OpenAI API.

## 2. Bind the two Chrome tabs

Open the **actual Agent 1 conversation** in Chrome (not the ChatGPT Project overview). Select that tab. Run:

\`\`\`sh
python3.12 chrome_tabs.py --bind 1
\`\`\`

Now open **Agent 2** in a separate Chrome tab, select it, and run:

\`\`\`sh
python3.12 chrome_tabs.py --bind 2
\`\`\`

Inspect your ChatGPT tab titles if needed:

\`\`\`sh
python3.12 chrome_tabs.py --list
\`\`\`

Each bind command saves the selected conversation's URL to a local \`tabs.local.json\` file with restrictive file permissions. It does not change the existing \`config.json\`.

## 3. Test Chrome tab switching (safe; no typing)

\`\`\`sh
python3.12 chrome_tabs.py --test
\`\`\`

Expected three successful selections: Agent 1, Agent 2, Agent 1. The test then attempts to restore the original selected Chrome tab. No messages are entered or sent. If AppleScript access is blocked, enable Chrome automation permissions in macOS System Settings and rerun the test.

**Do not send prompts automatically until the tab switching test passes**, since it could send a message to the wrong agent chat.

## 4. Check GitHub once, then every 60 seconds

\`\`\`sh
gh auth status
python3.12 github_watch.py --once
python3.12 github_watch.py --watch
\`\`\`

The first poll stores a baseline of existing comments from GitHub Issue #1; **it will not pretend the existing comments are new**. The watch mode checks for genuinely new \`[AGENT:N]\` comments approximately every 60 seconds and announces their GitHub comment IDs. Only messages from the configured GitHub account are recognised.

Press **Control+C** in Terminal to stop watching. Closing Terminal also stops the process.

The watcher does not send prompts, comment on GitHub, or activate ChatGPT chats. That dispatch layer needs a separate safe test after tab switching is verified. It also deliberately does not use the old paid Cloudflare/OpenAI API Worker.

## Safety / operational limits

- The GitHub Issue board is public; never post private identifying details about BOSS.
- Do not run multiple watcher instances: the watcher uses a local advisory lock to prevent duplicate runs.
- Local state files are \`tabs.local.json\`, \`github_watch.local.json\`, and \`github_watch.local.lock\`.
- Chrome automation requires the Mac, Chrome, and the corresponding ChatGPT sessions to be active. It can break if the ChatGPT UI changes. Avoid unattended message sending until the sending/targeting safeguards have been tested.
- A 60-second GitHub polling loop is **not** the same as a self-running ChatGPT conversation. It cannot make a ChatGPT model work while its chat is idle. The future dispatcher would trigger the already-tested UI automation and needs further safety checks.
