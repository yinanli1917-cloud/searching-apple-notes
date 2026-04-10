# searching-apple-notes — a Claude Code Skill for Apple Notes

> A Claude Code skill that turns your Apple Notes archive into a searchable second brain. You ask, Claude searches semantically, reads the relevant notes, and answers from your real prior thinking — no search box, no keyword guessing, no scrolling through years of notes.
>
> 把 Apple Notes 变成 Claude Code 可以检索的第二大脑。你只管问，Claude 自动做语义搜索、读出相关笔记、用你过去真实的思考来回答——不需要搜索框，不需要猜关键词，不需要在几年的笔记里翻找。

[English](#english) | [中文](#中文)

---

## English

### What it is

`searching-apple-notes` is a **Claude Code skill**. Once installed, you can ask Claude things like:

> "What did I write about typography last winter?"
>
> "Do I have any notes about that book on attention I read?"
>
> "Find my thinking on B2B onboarding friction."
>
> "Save this conversation as a note tagged #ideas."

…and Claude will quietly run a semantic search over your local Apple Notes archive, read the relevant notes, and answer with citations. Or, when you tell it to capture an insight, it will write a properly formatted note back into Apple Notes with your tags. You never type a search query, you never see the tool calls, you just have a conversation, and Claude knows what you've already thought — and remembers what you think next.

The skill is the **brain** — a `SKILL.md` file that teaches Claude *when* to search, *how* to phrase queries, *how* to interpret results, *how* to cite, and *when* to write a new note. The four helper Python scripts that ship inside the skill folder are the **hands** — they actually run BGE-M3 over your notes, talk to ChromaDB, and call AppleScript when a new note needs to be created. There is no MCP server involved in this skill. Claude Code invokes the scripts directly via Bash.

### Why it works well

Three things, working together:

**1. Semantic search, not keyword matching.** BGE-M3 is a multilingual embedding model that understands meaning. Searching for "burnout" finds notes about "exhaustion," "心累," and "running on fumes" even when none of those exact words appear in the query. For mixed Chinese-English notes — diary entries, design sketches, half-formed product ideas — it outperforms English-only embedders by a wide margin.

**2. Local, private, and incremental.** Your notes never leave your Mac. The embedding model runs on your CPU or GPU (≈10 seconds cold start, sub-second per query after that). The index is incremental, so a daily refresh on a 5,000-note archive finishes in seconds, not minutes. No API keys, no usage charges, no third-party servers reading your private thoughts.

**3. The skill teaches Claude judgment, not just commands.** A naive setup hands Claude a script and lets it flail — searching for the wrong things, fetching too few results, ignoring obvious context, never knowing when to refresh stale data. This skill includes an explicit *strategy*: when to search and when not to, how many results to fetch, how to phrase queries that actually find things, when to use a tag filter versus full-corpus search, when to refresh the index, how to cite results so you know exactly which note an answer came from. It's the difference between "Claude can technically search" and "Claude searches the right thing at the right time."

### What it feels like to use

Once installed, the skill is invisible. You just talk to Claude in English or Chinese:

> **You:** Did I take any notes about that book on attention I read last month?
>
> **Claude:** *(silently runs `vector_search.py "attention book notes" --after 2026-03-01`)*
>
> Yes — you have a note titled "Stolen Focus, chapters 1–3" from March 14, and another titled "fragmented attention vs flow" from March 22. The first captures your reaction to Hari's argument about social media disrupting deep reading. The second is your own elaboration where you note that flow states require a particular kind of friction-free attention that…

> **You:** 帮我找一下我写过的关于产品定位的笔记
>
> **Claude:** *(silently runs `vector_search.py "产品定位"`)*
>
> 我在你的备忘录里找到 4 条相关的笔记：…

> **You:** Save this whole conversation as a note tagged #strategy
>
> **Claude:** *(silently runs `create_note.py "Notes on attention and flow" "..." --folder "Notes"`)*
>
> Saved as a new note in your "Notes" folder with the #strategy tag. You'll see it in Apple Notes within a few seconds.

You never see the tool calls. You just ask, and Claude answers from your actual prior thinking — and writes new thinking back into the same archive. Because BGE-M3 is bilingual, you can ask in either language and get hits across notes written in either language.

### Install

**Step 1 — set up the parent repository.** This skill depends on the BGE-M3 model and the SQLite-plus-ChromaDB pipeline shipped in the parent repo. Follow the setup section in the [main README](../../README.md):

```bash
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp
pip3 install -r requirements.txt
python3.12 scripts/export_notes_fixed.py    # one-time export
python3.12 scripts/indexer.py                # one-time vector index build (3-5 min)
```

The first index build downloads the BGE-M3 model (~2 GB) and embeds your existing notes. Subsequent syncs are incremental and take seconds.

**Step 2 — drop the skill into Claude Code.** Pick one of:

```bash
# Project-level (only this project sees the skill)
mkdir -p .claude/skills
cp -r skills/searching-apple-notes .claude/skills/

# Global (all your projects see the skill)
mkdir -p ~/.claude/skills
cp -r skills/searching-apple-notes ~/.claude/skills/
```

That's it. Restart Claude Code, ask it to find something in your notes, and it will.

### How the skill is structured

```
searching-apple-notes/
├── SKILL.md              # The instructions Claude reads when the skill activates
├── README.md             # This file (human-facing docs)
└── scripts/
    ├── vector_search.py  # Semantic search CLI (BGE-M3 + ChromaDB)
    ├── get_note.py       # Fetch full content of a single note by index
    ├── create_note.py    # Write a new note from markdown body
    └── sync_index.py     # One-shot pipeline: export + tag bridge + incremental index
```

`SKILL.md` is the brain. It contains the trigger conditions, the script invocation patterns, the search strategy, and the dialogue-to-note workflow. Claude reads it on every turn where the trigger conditions match.

The four scripts are the hands. They use `__file__`-based path resolution, so they figure out the parent repo's location automatically — they work no matter where you cloned the repo.

### Why these four scripts

| Script | What it does | When Claude calls it |
|--------|--------------|---------------------|
| `vector_search.py` | Runs semantic vector search with optional tag/folder/date filters. Returns JSON. | Whenever the user asks Claude to find or recall something from their notes. |
| `get_note.py` | Fetches the full plain-text content of a single note by Notes.app index. | When the search snippet isn't enough and Claude needs the full note body. |
| `create_note.py` | Creates a new Apple Note from a markdown body via AppleScript. Hashtags become real Apple Notes hashtags. | When the user says "save this to notes" or "save this insight". |
| `sync_index.py` | Re-exports from Notes.app, bridges native hashtags from `NoteStore.sqlite`, then runs an incremental vector index update. | When the user says they just added a note that search isn't finding, or when `--stats` shows the index is stale. |

### The clever bit: bridging native Apple Notes hashtags

Apple Notes has its own native hashtag system, separate from any plain `#text` you might write yourself. Native hashtags are stored in `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`, in a table called `ZICCLOUDSYNCINGOBJECT`, where rows with `ZTYPEUTI1 = 'com.apple.notes.inlinetextattachment.hashtag'` are the tag attachments. Each tag row links to its parent note via `ZNOTE1 → Z_PK`.

`sync_index.py` reads that table, joins it back to our SQLite mirror (our note IDs end in `/pN` where `N` is the same `Z_PK`), and writes the native tags into our database so they can be used as filters. This means `vector_search.py --tag MyTag` actually finds notes you tagged in the Apple Notes app itself, not just notes where you happened to type `#MyTag` as plain text.

### Privacy

Everything is local. The BGE-M3 model runs on your Mac. The vector index is a folder on your Mac. The SQLite mirror of your notes is a file on your Mac. Nothing is sent to any third-party server. No API keys are required. The only network traffic the skill ever generates is the one-time download of the BGE-M3 model from Hugging Face during initial setup.

### License

MIT, same as the parent repository.

---

## 中文

### 这是什么

`searching-apple-notes` 是一个 **Claude Code 技能包**。安装好之后，你可以直接这样问 Claude：

> "我去年冬天写过关于排版的笔记吗？"
>
> "我读过的那本关于注意力的书，我有做笔记吗？"
>
> "帮我找一下我对 B2B 产品冷启动的思考。"
>
> "把这段对话存成笔记，打 #ideas 标签。"

……Claude 会默默地在你本地的 Apple Notes 上做语义搜索，读出相关的笔记，然后带着引用来回答你。或者当你让它捕捉一个洞察时，它会用合适的格式把笔记写回 Apple Notes，并加上你指定的标签。你不需要敲一个搜索关键词，也看不到工具调用，你只是在跟 Claude 聊天，而 Claude 既知道你过去想过什么，也能记下你现在新想到的东西。

技能包是**大脑**——一个 `SKILL.md` 文件，教 Claude **什么时候**该搜、**怎么**写查询、**怎么**理解返回结果、**怎么**引用、**什么时候**该写一条新笔记。技能包文件夹里附带的四个 Python 辅助脚本是**手**——它们在你的笔记上跑 BGE-M3、跟 ChromaDB 对话、需要写新笔记时调用 AppleScript。本技能包不涉及任何 MCP 服务器。Claude Code 通过 Bash 直接调用这些脚本。

### 为什么效果好

三个东西凑在一起：

**1. 语义检索，不是关键词匹配。** BGE-M3 是一个多语言嵌入模型，它真的理解意思。搜"职业倦怠"能找到写"心累"、"exhaustion"、"再也撑不住"的笔记，哪怕这些字一个都没出现过。对中英文混杂的笔记——日记、设计草稿、半成形的产品想法——它比纯英文训练的嵌入模型好得多。

**2. 本地、私密、增量。** 你的笔记永远不离开你的 Mac。嵌入模型在你的 CPU 或 GPU 上跑（首次冷启动约 10 秒，之后每次查询不到 1 秒）。索引是增量的，所以一个 5000 条笔记的语料库每日刷新只需要几秒钟，而不是几分钟。不需要 API key，不需要付费，不需要任何第三方服务器读取你的私人想法。

**3. 技能包教 Claude 判断力，而不只是命令。** 朴素的做法是给 Claude 一个脚本然后让它自己瞎试——搜错东西、取太少结果、忽略明显的上下文、永远不知道什么时候该刷新过期的数据。这个技能包内置了一套明确的**策略**：什么时候该搜、什么时候不该搜、一次取几条结果、怎么把模糊的问题改写成能命中的查询、什么时候该用标签过滤、什么时候该全库搜、什么时候该刷新索引、怎么在回答里引用结果让你知道答案到底来自哪条笔记。这是"Claude 技术上能搜索"和"Claude 在对的时刻搜对的东西"之间的差别。

### 用起来是什么感觉

安装好之后，技能包是隐形的。你就用中文或英文跟 Claude 说话：

> **你：** 我上个月写过关于注意力的那本书的笔记吗？
>
> **Claude：** *(在后台调用 `vector_search.py "注意力 书 笔记" --after 2026-03-01`)*
>
> 有的——你 3 月 14 日有一篇笔记叫《Stolen Focus 第 1-3 章》，3 月 22 日还有一篇叫《碎片化注意力 vs 心流》。第一篇记录了你对作者关于社交媒体破坏深度阅读这个论点的反应；第二篇是你自己的延伸思考，你在里面提到心流状态需要一种特别的、没有摩擦的注意力……

> **你：** Help me find notes about product positioning
>
> **Claude：** *(在后台调用 `vector_search.py "product positioning"`)*
>
> Found 4 relevant notes in your archive: …

> **你：** 把刚才整段对话存成笔记，打 #strategy 标签
>
> **Claude：** *(在后台调用 `create_note.py "关于注意力与心流的对话" "..." --folder "Notes"`)*
>
> 已经存到你的"Notes"文件夹里，加了 #strategy 标签。几秒内会在 Apple Notes 里看到。

你看不到工具调用。你只是问问题，Claude 用你过去真实的思考来回答——同时把新的思考写回同一个备忘录库。因为 BGE-M3 是双语的，你用中文或英文问都能找到对应语言写的笔记。

### 安装

**第一步——配置好父仓库。** 本技能依赖父仓库里的 BGE-M3 模型和 SQLite + ChromaDB 流水线。按[主 README](../../README.md) 的安装步骤走一遍：

```bash
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp
pip3 install -r requirements.txt
python3.12 scripts/export_notes_fixed.py    # 一次性导出
python3.12 scripts/indexer.py                # 一次性建立向量索引（3-5 分钟）
```

第一次建索引时会下载 BGE-M3 模型（约 2 GB）并为你已有的笔记生成向量。之后的同步都是增量的，只需要几秒钟。

**第二步——把技能包丢给 Claude Code。** 二选一：

```bash
# 项目级别（只有当前项目能看到这个技能）
mkdir -p .claude/skills
cp -r skills/searching-apple-notes .claude/skills/

# 全局（所有项目共享这个技能）
mkdir -p ~/.claude/skills
cp -r skills/searching-apple-notes ~/.claude/skills/
```

到此为止。重启 Claude Code，让它找点笔记，它就会找。

### 技能包的结构

```
searching-apple-notes/
├── SKILL.md              # Claude 在技能激活时读取的指令文件
├── README.md             # 本文件（给人看的文档）
└── scripts/
    ├── vector_search.py  # 语义搜索 CLI（BGE-M3 + ChromaDB）
    ├── get_note.py       # 按 Notes.app 序号获取一条笔记的完整内容
    ├── create_note.py    # 从 markdown 正文创建一条新笔记
    └── sync_index.py     # 一键流水线：导出 + 标签桥接 + 增量索引
```

`SKILL.md` 是大脑。里面有触发条件、脚本调用方式、搜索策略，和"对话→洞察→笔记"的工作流程。每次匹配触发条件时 Claude 都会读它。

四个脚本是手。它们都用 `__file__` 来定位路径，会自动算出父仓库的位置——你把仓库克隆到任何地方都能跑。

### 这四个脚本各自做什么

| 脚本 | 做什么 | Claude 什么时候调用 |
|------|--------|-------------------|
| `vector_search.py` | 跑语义向量搜索，可选标签/文件夹/日期过滤。返回 JSON。 | 用户让 Claude 在笔记里找东西、回忆某段思考时。 |
| `get_note.py` | 按 Notes.app 序号取一条笔记的完整纯文本。 | 当搜索返回的摘要不够、Claude 需要完整笔记内容时。 |
| `create_note.py` | 通过 AppleScript 从 markdown 正文创建一条新的 Apple Note。`#TagName` 自动变成原生 hashtag。 | 用户说"存到笔记"或"把这个洞察存下来"时。 |
| `sync_index.py` | 重新从 Notes.app 导出、桥接原生 hashtag、跑增量向量索引更新。 | 用户说他刚加了一条笔记但搜索找不到时；或者 `--stats` 显示索引落后时。 |

### 一个有意思的细节：桥接 Apple Notes 的原生 hashtag

Apple Notes 有它自己的原生 hashtag 系统，跟你随手在正文里敲的 `#text` 不是一回事。原生 hashtag 存在 `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite` 里，表叫 `ZICCLOUDSYNCINGOBJECT`，符合 `ZTYPEUTI1 = 'com.apple.notes.inlinetextattachment.hashtag'` 的行就是 tag attachment。每个 tag 行通过 `ZNOTE1 → Z_PK` 链回它所属的笔记。

`sync_index.py` 读这张表，跟我们自己的 SQLite 镜像做 join（我们的笔记 ID 末尾是 `/pN`，这个 `N` 就是同一个 `Z_PK`），然后把原生 tag 写入我们的数据库，这样 tag 就能用作过滤条件了。这意味着 `vector_search.py --tag MyTag` 真的能找到你在 Apple Notes 应用里打过 tag 的笔记，不只是那些你随手敲了 `#MyTag` 的笔记。

### 隐私

一切都在本地。BGE-M3 模型在你的 Mac 上跑。向量索引是你 Mac 上的一个文件夹。笔记的 SQLite 镜像是你 Mac 上的一个文件。任何东西都不会发送到任何第三方服务器。不需要 API key。这个技能产生的唯一一次网络流量，是初次安装时从 Hugging Face 下载 BGE-M3 模型的那一次。

### 协议

MIT，与父仓库一致。
