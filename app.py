"""
留言墙 —— 动态网站演示
========================
一个真实的留言板：分享日常、推荐书单、记录复盘、
说说开心或烦恼的事。每个人都能看到别人的留言并回复。

必须有服务器才能运行 → 这就是动态网站。

启动: python app.py
访问: http://localhost:5000
"""

from flask import Flask, request, redirect, url_for, make_response
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = "board.db"

# ── 分类配置 ──
CATEGORIES = {
    "daily":    {"icon": "📝", "label": "今日复盘"},
    "book":     {"icon": "📚", "label": "推荐书单"},
    "happy":    {"icon": "😊", "label": "开心的事"},
    "sad":      {"icon": "🌧️", "label": "烦恼倾诉"},
    "thought":  {"icon": "💭", "label": "碎碎念"},
}


# ── 数据库 ──
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname   TEXT NOT NULL,
            category   TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS replies (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id    INTEGER NOT NULL,
            nickname   TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
    """)
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now().isoformat()


def fmt_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        now = datetime.now()
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return "刚刚"
        if secs < 3600:
            return f"{secs // 60} 分钟前"
        if secs < 86400:
            return f"{secs // 3600} 小时前"
        return dt.strftime("%m月%d日 %H:%M")
    except Exception:
        return iso_str


# ── 页面模板 ──
def render(body, title="留言墙"):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh}}
.wrap{{max-width:680px;margin:0 auto;padding:20px 16px}}
header{{text-align:center;padding:30px 0 10px}}
header h1{{font-size:26px;background:linear-gradient(135deg,#6366f1,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
header p{{color:#9ca3af;font-size:13px;margin-top:6px}}
.nav{{display:flex;justify-content:center;gap:16px;margin:16px 0 20px}}
.nav a{{color:#6366f1;text-decoration:none;font-size:14px;font-weight:600;padding:6px 16px;border-radius:8px;background:#ede9fe}}
.nav a:hover{{background:#ddd6fe}}
.card{{background:#fff;border-radius:14px;padding:20px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.06);transition:box-shadow .2s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.1)}}
.tag{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;margin-right:6px}}
.tag-daily{{background:#dbeafe;color:#2563eb}}
.tag-book{{background:#fef3c7;color:#d97706}}
.tag-happy{{background:#d1fae5;color:#059669}}
.tag-sad{{background:#fce7f3;color:#db2777}}
.tag-thought{{background:#e0e7ff;color:#6366f1}}
.post-head{{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}}
.post-head .name{{font-weight:700;font-size:15px}}
.post-head .time{{font-size:12px;color:#9ca3af;margin-left:auto}}
.post-body{{font-size:15px;line-height:1.8;color:#374151;white-space:pre-wrap}}
.post-foot{{display:flex;gap:16px;margin-top:12px;padding-top:10px;border-top:1px solid #f3f4f6}}
.post-foot a{{color:#9ca3af;font-size:13px;text-decoration:none}}
.post-foot a:hover{{color:#6366f1}}
.btn{{display:inline-block;padding:12px 28px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer}}
.btn:hover{{opacity:.9}}
.btn-sm{{padding:8px 18px;font-size:13px}}
input[type=text],textarea,select{{width:100%;padding:12px;border:2px solid #e5e7eb;border-radius:10px;font-size:14px;font-family:inherit;outline:none;transition:border .2s}}
input:focus,textarea:focus,select:focus{{border-color:#6366f1}}
textarea{{height:140px;resize:vertical}}
select{{cursor:pointer;background:#fff}}
label{{display:block;font-size:13px;font-weight:600;color:#6b7280;margin-bottom:6px}}
.field{{margin-bottom:14px}}
.reply-box{{background:#f9fafb;border-radius:10px;padding:14px;margin-bottom:10px}}
.reply-box .rhead{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
.reply-box .rname{{font-weight:600;font-size:13px;color:#6366f1}}
.reply-box .rtime{{font-size:11px;color:#9ca3af}}
.reply-box .rbody{{font-size:14px;color:#4b5563;line-height:1.6;white-space:pre-wrap}}
.reply-to{{color:#9ca3af;font-size:13px;margin-bottom:4px}}
.reply-to strong{{color:#6366f1}}
.empty{{text-align:center;padding:40px;color:#9ca3af}}
.stat-bar{{display:flex;gap:20px;justify-content:center;margin:12px 0;flex-wrap:wrap}}
.stat-item{{font-size:13px;color:#6b7280}}
.stat-item strong{{color:#6366f1}}
.cat-filters{{display:flex;gap:8px;justify-content:center;margin:10px 0 18px;flex-wrap:wrap}}
.cat-filters a{{font-size:12px;padding:4px 12px;border-radius:20px;text-decoration:none;color:#6b7280;background:#f3f4f6}}
.cat-filters a:hover,.cat-filters a.active{{background:#6366f1;color:#fff}}
footer{{text-align:center;padding:30px 0;color:#d1d5db;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>留言墙</h1>
    <p>分享今天 · 推荐好书 · 记录复盘 · 说说心情</p>
  </header>
  <div class="nav">
    <a href="/">🏠 全部留言</a>
    <a href="/post">✏️ 发一条</a>
  </div>
  {body}
  <footer>动态网站 · 数据存在服务器 · 多人实时共享</footer>
</div>
</body>
</html>"""


# ── 路由 ──

@app.route("/")
def index():
    """首页：显示所有留言"""
    cat = request.args.get("cat", "")
    conn = get_db()

    if cat and cat in CATEGORIES:
        posts = conn.execute(
            "SELECT * FROM posts WHERE category=? ORDER BY created_at DESC", (cat,)
        ).fetchall()
    else:
        posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()

    # 每条留言的回复数
    counts = {}
    for p in posts:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM replies WHERE post_id=?", (p["id"],)
        ).fetchone()
        counts[p["id"]] = row["c"]

    total_posts = conn.execute("SELECT COUNT(*) as c FROM posts").fetchone()["c"]
    total_replies = conn.execute("SELECT COUNT(*) as c FROM replies").fetchone()["c"]
    conn.close()

    # 统计栏
    stats = f"""
  <div class="stat-bar">
    <span class="stat-item">共 <strong>{total_posts}</strong> 条留言</span>
    <span class="stat-item"><strong>{total_replies}</strong> 条回复</span>
  </div>"""

    # 分类筛选
    filters = '<div class="cat-filters"><a href="/" class="{cls_all}">全部</a>'.format(
        cls_all="active" if not cat else ""
    )
    for key, val in CATEGORIES.items():
        active = "active" if cat == key else ""
        filters += f' <a href="/?cat={key}" class="{active}">{val["icon"]} {val["label"]}</a>'
    filters += "</div>"

    # 留言列表
    if posts:
        cards = ""
        for p in posts:
            cat_info = CATEGORIES.get(p["category"], {"icon": "💬", "label": p["category"]})
            rc = counts.get(p["id"], 0)
            reply_text = f"💬 回复 ({rc})" if rc > 0 else "💬 回复"
            content_preview = p["content"] if len(p["content"]) <= 150 else p["content"][:150] + "..."
            cards += f"""
  <div class="card">
    <div class="post-head">
      <span class="tag tag-{p['category']}">{cat_info['icon']} {cat_info['label']}</span>
      <span class="name">{p['nickname']}</span>
      <span class="time">{fmt_time(p['created_at'])}</span>
    </div>
    <div class="post-body">{content_preview}</div>
    <div class="post-foot">
      <a href="/post/{p['id']}">{reply_text}</a>
      <a href="/post/{p['id']}">查看详情 →</a>
    </div>
  </div>"""
    else:
        cards = '<div class="empty card">还没有留言，<a href="/post">发第一条</a>吧！</div>'

    return render(stats + filters + cards)


@app.route("/post", methods=["GET", "POST"])
def post():
    """发留言"""
    if request.method == "GET":
        cat_options = ""
        for key, val in CATEGORIES.items():
            cat_options += f'<option value="{key}">{val["icon"]} {val["label"]}</option>'

        return render(f"""
  <div class="card">
    <form method="POST" action="/post">
      <div class="field">
        <label>你的昵称</label>
        <input type="text" name="nickname" placeholder="叫什么都行" required>
      </div>
      <div class="field">
        <label>分类</label>
        <select name="category">{cat_options}</select>
      </div>
      <div class="field">
        <label>想说的话</label>
        <textarea name="content" placeholder="今天的复盘、最近读的书、开心或烦恼的事…" required></textarea>
      </div>
      <button type="submit" class="btn">发布留言</button>
    </form>
  </div>""", "发留言")

    # POST 处理
    nickname = request.form.get("nickname", "").strip() or "匿名"
    category = request.form.get("category", "thought")
    content = request.form.get("content", "").strip()
    if not content:
        return redirect(url_for("post"))
    if category not in CATEGORIES:
        category = "thought"

    conn = get_db()
    conn.execute(
        "INSERT INTO posts (nickname, category, content, created_at) VALUES (?,?,?,?)",
        (nickname, category, content, now_iso())
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>")
def detail(post_id):
    """留言详情 + 回复"""
    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return render('<div class="empty card">留言不存在</div>', "404"), 404

    replies = conn.execute(
        "SELECT * FROM replies WHERE post_id=? ORDER BY created_at ASC", (post_id,)
    ).fetchall()
    conn.close()

    cat_info = CATEGORIES.get(post["category"], {"icon": "💬", "label": post["category"]})

    # 留言正文
    body = f"""
  <div class="card">
    <div class="post-head">
      <span class="tag tag-{post['category']}">{cat_info['icon']} {cat_info['label']}</span>
      <span class="name">{post['nickname']}</span>
      <span class="time">{fmt_time(post['created_at'])}</span>
    </div>
    <div class="post-body">{post['content']}</div>
  </div>"""

    # 回复列表
    body += f"""
  <div class="card">
    <h3 style="font-size:16px;margin-bottom:14px">💬 回复 ({len(replies)})</h3>"""

    if replies:
        for r in replies:
            body += f"""
    <div class="reply-box">
      <div class="rhead">
        <span class="rname">{r['nickname']}</span>
        <span class="rtime">{fmt_time(r['created_at'])}</span>
      </div>
      <div class="rbody">{r['content']}</div>
    </div>"""
    else:
        body += '<div class="empty" style="padding:20px">还没有回复，说点什么吧 ↓</div>'

    body += """
  </div>"""

    # 回复表单
    body += f"""
  <div class="card">
    <h3 style="font-size:16px;margin-bottom:14px">✍️ 写回复</h3>
    <form method="POST" action="/post/{post_id}/reply">
      <div class="field">
        <label>你的昵称</label>
        <input type="text" name="nickname" placeholder="叫什么都行" required>
      </div>
      <div class="field">
        <label>回复内容</label>
        <textarea name="content" style="height:100px" placeholder="说点什么…" required></textarea>
      </div>
      <button type="submit" class="btn btn-sm">发送回复</button>
    </form>
  </div>"""

    return render(body, f"{post['nickname']}的留言")


@app.route("/post/<int:post_id>/reply", methods=["POST"])
def reply(post_id):
    """提交回复"""
    nickname = request.form.get("nickname", "").strip() or "匿名"
    content = request.form.get("content", "").strip()
    if not content:
        return redirect(url_for("detail", post_id=post_id))

    conn = get_db()
    conn.execute(
        "INSERT INTO replies (post_id, nickname, content, created_at) VALUES (?,?,?,?)",
        (post_id, nickname, content, now_iso())
    )
    conn.commit()
    conn.close()
    return redirect(url_for("detail", post_id=post_id))


# ── 启动 ──
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print()
    print("=" * 50)
    print("  留言墙 —— 动态网站")
    print(f"  http://localhost:{port}")
    print("=" * 50)
    print()
    app.run(debug=False, host="0.0.0.0", port=port)
