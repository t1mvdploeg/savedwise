# Phase 2: Links

Goal: `<kb>/links.tsv`, one post per line: `<collection><TAB><url>`. The collection is a short slug the user recognises (`ig-ai`, `tt-dev`). Append only; skip URLs whose id is already in the file.

## Option A: the user pastes links

Accept any mix of URLs, one per line or separated by spaces. Keep only links to a single post (`/reel/`, `/p/`, `/video/`, `/photo/`, or a TikTok short link); tell the user which links you dropped, such as profile or collection pages. Ask for a collection name if none is given (default `unsorted`). Drop tracking parameters (`?igsh=…`, `?is_from_webapp=…`). Keep short links (`vm.tiktok.com/…`) as they are; yt-dlp resolves them.

## Option B: scroll a saved collection with Claude in Chrome

1. Ask which collections to process. Have the user open the first one in Chrome while logged in: on Instagram, profile → Saved → the collection; on TikTok, profile → Favorites → Collections → the collection. Only collect from collections the user named.
2. Use one visible tab. A background tab throttles timers and the scroll loop times out.
3. Run this in the page. It keeps links in a `Set` while scrolling, because Instagram only renders the visible part of the grid, and stops when four scrolls in a row add nothing. Rerunning continues the same set.

```js
(async () => {
  const seen = new Set(window.__savedwise || []);
  const pick = () => document
    .querySelectorAll('a[href*="/reel/"], a[href*="/p/"], a[href*="/video/"], a[href*="/photo/"]')
    .forEach(a => seen.add(a.href.split('?')[0]));
  for (let still = 0, last = -1; still < 4; ) {
    pick();
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 1500));
    still = seen.size === last ? still + 1 : 0;
    last = seen.size;
  }
  pick();
  window.__savedwise = [...seen];
  return window.__savedwise.length;
})()
```

4. Read the links in batches of 50 with `window.__savedwise.slice(0, 50).join('\n')`. The tool may block output that looks like base64, such as Instagram shortcodes. Then return each URL with spaces between the characters and remove them afterwards:

```js
window.__savedwise.slice(0, 50).map(u => u.split('').join(' ')).join(' | ')
```

5. Compare the count with what the collection shows. If it is lower, change `1500` to `3000` and run step 3 again.
6. Append to `links.tsv` with the collection slug, then clear the set (`window.__savedwise = []`) before the next collection.

Report the number of new links per collection.
