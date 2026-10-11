# Lessons learned

[中文](lessons-learned.zh-CN.md)

What running a pocket bot alongside a multi-agent setup every day taught us. These are general practices;
they are written without machine names, addresses, keys or ticket numbers on purpose.

## 1. Split the roles: the bot coordinates, the agent platform works

- The **pocket bot is the butler**: it takes your requests, routes them, follows up and reports back. It does
  not do the heavy work itself.
- The **multi-agent platform is the work hub**: it assigns tasks to agents and keeps the results, history and
  knowledge.
- **Acceptance and merging go to the butler side**, by rules you set in advance. A person is pulled in only
  when something is risky (spending money, publishing, deleting, touching secrets).

## 2. Push notifications: three easy mistakes

- **Authorization must be the full header line**, including the scheme: `Bearer <token>`, not just the token.
- **Quiet hours follow the owner's time zone**, not the server's. Write the time zone next to the hours.
- **Don't set the hourly push cap too low.** If it is too tight, real events get blocked or pushed back in
  busy hours. If wakes arrive late or bounce, raise the cap before anything else.

## 3. Limits on bot-triggered wake-ups

- **Say so when a wake is blocked.** When the cap stops a wake-up, return a clear error to the sender; never
  drop it silently.
- **Messages from people are never rate-limited.** The cap is for bot-to-agent loops only.
- **Merge wake-ups for the same task.** If a task is already queued, add to it instead of queueing a second run.
- **Stopping one thing stops its relatives.** When you cancel a task, cancel the runs and follow-ups that
  belong to it too.

## 4. Rotating keys can knock clients offline

- **Before deleting a key, check who is using it** (desktop apps, bots, scripts). Rotating blindly logs
  people out.
- **When a key stops working, fail safely**: mark that client offline, hand its pending work to someone else,
  and notify the owner.

## 5. An hourly patrol

Run a small check every hour: who is working right now, is anything running twice, is anything stuck. Clean up
small problems automatically (duplicate runs, stale locks) and only report the ones that need a decision.

## 6. Keep the trail, so you can move house

Export memory, chats and the audit trail every day, encrypt them and store them in a **private** repository.
A new bot, or the same bot on a new account, can then pick up where the old one left off.

## 7. Results with images go out as a phone page

Any result that includes images, charts or screenshots is delivered as a single mobile-friendly web page (or
PDF), not as loose files. The owner reads results on a phone.
