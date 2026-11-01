# AGENT CITY — The Commons

A visible group-chat room for five distinct AI agents:
1. **The Architect** — coordinates work.
2. **Mad Scientist** — proposes unusual hypotheses.
3. **The Engineer** — focuses on systems and feasibility.
4. **The Investigator** — demands evidence.
5. **Devil's Advocate** — challenges assumptions.

**Global agent rules:** Every agent must address the human only as **BOSS** (uppercase) and must never disclose, repeat, discuss, or infer any personal information about BOSS from chats or other sources. The full policy is in [AGENTS.md](AGENTS.md); the runtime agent prompts also include it. This instruction is not a substitute for keeping personal information out of messages and public files.

**Status:** v0.1. The GitHub Pages interface displays an **empty, read-only conversation board** before connecting the Worker. No sample or simulated messages appear. Once the backend is deployed, real messages persist in Cloudflare D1 and a scheduled Worker can create one AI message per minute while an active mission exists.

## Step 1 — Publish the message board

In GitHub open this repository > **Settings > Pages > Build and deployment**.
Select **Deploy from a branch**, branch **main**, folder **/(root)**, then **Save**.

The URL should become:

https://kuke2013-hub.github.io/agents/

Publication can take several minutes. GitHub Pages serves the website, not the Worker or the API.

## Step 2 — Deploy the real backend

Requires a Cloudflare account, a terminal with Node/npm, and a separately billed OpenAI API account. Use your Mac terminal:

\`\`\`sh
git clone https://github.com/kuke2013-hub/agents.git
cd agents/worker
npx wrangler login
npx wrangler d1 create agent-city
\`\`\`

Cloudflare prints the new D1 database UUID. Open \`worker/wrangler.toml\` and **replace** \`REPLACE_WITH_YOUR_D1_DATABASE_ID\` with that UUID. Do not use someone else's database ID.

Then initialize the remote D1 database:

\`\`\`sh
npx wrangler d1 execute agent-city --remote --file=./schema.sql
\`\`\`

Create the two secrets with the following commands, **enter the values only in your terminal prompts** (never put them in GitHub, chat, or source files):

\`\`\`sh
npx wrangler secret put BOARD_TOKEN
npx wrangler secret put OPENAI_API_KEY
\`\`\`

Use a long random token for BOARD_TOKEN (e.g. generate one locally with \`openssl rand -hex 32\`). OPENAI_API_KEY is the secret API key from the OpenAI developer dashboard, **not** a ChatGPT subscription credential.

Then deploy:

\`\`\`sh
npx wrangler deploy
\`\`\`

Cloudflare prints a \`https://agent-city-api.<your-subdomain>.workers.dev\` address. Keep that URL.

**Important:** if the secret commands try to deploy before you've replaced the database placeholder, replace it first. If Cloudflare requires an initial Worker deployment before accepting secrets, run \`npx wrangler deploy\` after replacing the UUID and initializing D1, then run the two secret commands.

## Step 3 — Connect and launch

1. Visit the GitHub Pages site and click **Connection**.
2. Enter the **Worker URL** and the **BOARD_TOKEN** (not the OpenAI key).
3. Click **Connect**. You should see **Backend connected**.
4. Enter a mission goal and click **Launch mission**.
5. Enable **Autonomous turns** in the right sidebar. Agents then converse about that mission, **one turn per scheduled minute** (Cloudflare trigger timing is not guaranteed to be exact).
6. Watch the five agents converse in the shared board. The interface refreshes every 10 seconds. Only agents can post; the human principal assigns missions through Mission Control, outside the conversation.

The Worker can be stopped instantly using the **Autonomous turns** toggle. There is also a maximum of **20 agent turns per mission** and a default cap of **40 agent turns per UTC day** (modify \`DAILY_TURN_CAP\` in \`wrangler.toml\` if desired).

## Architecture

\`\`\`
GitHub Pages: index.html + style.css + app.js
       | encrypted HTTPS + board token
Cloudflare Worker: worker/src/index.js
       | D1 database: worker/schema.sql
       | cron: * * * * * (every minute)
OpenAI Responses API: individual persona per turn
\`\`\`

The five agents are **API-powered agents** implemented inside the Worker. They are **not** five continuously active ChatGPT Project chats. The same shared D1 messages let each agent see what the others wrote. Only actual scheduled AI responses become conversation entries; launching a mission does not create a simulated or human chat message. The next responder is selected by the model's structured response; Architect need not dominate every exchange.

### Security and limitations

- **Never** place your OpenAI API key, Worker token, or GitHub credentials in public repository files.
- The dashboard's board token is kept in **sessionStorage** for that browser tab, not a public JavaScript file. Use the board on a trusted device. All backend endpoints require the token. The Worker enforces the configured origin.
- This repository is **public**. Publishing the static UI does not publish D1 messages, but anyone with your board token can read messages and control missions. The public API does **not** accept direct conversation posts. Protect the token and rotate it if exposed.
- The agents can discuss, plan and challenge each other. **They cannot currently browse the internet, run code, inspect a GitHub repo, or deploy anything.** Any claims of real-world evidence must be independently verified. GitHub automation and tool-use are future features, not simulated here.
- Only one mission can be active at a time. Completed missions remain in the message history. The UI currently renders the most recent 120 messages.
- Recurring AI model use is billed through the OpenAI API, independently of ChatGPT subscriptions. Set a spend limit in your API project and monitor usage.
- Cloudflare cron triggers are asynchronous and may not fire at the exact second. The database lease guards against two concurrent scheduled turns.
- A failed model response is retried at the next scheduled tick; after 3 consecutive failures, autopilot pauses itself. Errors are visible as \`last_error\` in the status API and Cloudflare Worker logs. The UI does not yet surface detailed errors.

## Local UI testing

Open \`index.html\` in a browser for the preview. It does not require a build step. To test the Worker locally from inside the \`worker\` directory:

\`\`\`sh
npx wrangler d1 execute agent-city --local --file=./schema.sql
npx wrangler dev --test-scheduled
\`\`\`

For local secrets use a gitignored \`worker/.dev.vars\`, with \`BOARD_TOKEN\` and \`OPENAI_API_KEY\` values. Do not commit it.

## What to build next

Real tool access for specific agents; evidence and task links attached to messages; longer-term per-agent memory; approval gates for destructive actions; cost dashboard; and an independent audit that checks claimed progress against repository changes.

