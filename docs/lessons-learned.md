# Lessons learned

[中文](lessons-learned.zh-CN.md)

What running a pocket bot alongside a multi-agent setup every day taught us. These are general practices;
they are written without machine names, addresses, keys or ticket numbers on purpose.

## 1. Split the offices: the butler coordinates, employees work

One device is one office, with agents as its employees. The owner gives goals; the butler contacts offices,
follows up and brings back a summary. This is the [office model](office-model.md), not a claim that every
device or assistant has already been integrated. Only Grok Bot + Multica is verified; webhook wake-up is in
live testing, while Dots, Muse, Cue and other local-agent integrations are untested.

- The **pocket bot is the butler**: it takes your requests, hands work to the relevant office, follows up and reports back. It does
  not do the heavy work itself.
- The **multi-agent platform is the work hub**: it assigns tasks to agents and keeps the results, history and
  knowledge.
- **Acceptance and merging go to the butler side**, by rules you set in advance. A person is pulled in only
  when something is risky (spending money, publishing, deleting, touching secrets).

## 2. Push notifications: three easy mistakes

- **The Authorization header value includes the scheme:** set it to `Bearer <token>`, not just the token.
- **Quiet hours follow the owner's time zone**, not the server's. Write the time zone next to the hours.
- **Don't set the hourly push cap too low.** If it is too tight, real events get blocked or pushed back in
  busy hours. If wake-ups arrive late or are blocked, check the reason first. Raise the cap when legitimate events are hitting it.

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

## 6. Keep project memory for future device changes

Employees should leave useful decisions and experience in project memory. Tarot, toB, self-media and school
are the areas whose accumulated knowledge Kun wants to keep.

**Automatic Google Drive backups are in progress:** Grok Bot every **2 days**, Multica every **7 days**.
These are intended schedules, not completed automation. Continuing after changing devices or the general
manager is a design goal; recovery is unverified. See [memory and backup status](office-model.md#memory-and-backup-status).

## 7. Results with images go out as a phone page

Any result that includes images, charts or screenshots is delivered as a single mobile-friendly web page (or
PDF), not as loose files. The owner reads results on a phone.
