#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  🚀 GITHUB FOLDER UPLOADER - ULTRA PRO v3.0                    ║
║  Full Feature: Upload, Edit, Delete, Create Repo, Drag & Drop  ║
║  100% Fixed • Zero Crash • Modern Dark UI                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import threading
import webbrowser
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ── Auto-install PyGithub ──
try:
    from github import Github, GithubException
except ImportError:
    import subprocess
    print("📦 Installing PyGithub...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyGithub"])
    from github import Github, GithubException

# ── Optional Drag & Drop ──
DND_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    pass

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".github_uploader_v3.json")


# ══════════════════════════════════════════════════════════════
#  TOOLTIP (Pure Tkinter - No External Dependency)
# ══════════════════════════════════════════════════════════════
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, e=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        frame = tk.Frame(tw, bg="#30363d", bd=1)
        frame.pack()
        tk.Label(frame, text=self.text, bg="#161b22", fg="#f0f6fc",
                font=("Segoe UI", 9), padx=8, pady=4, justify="left").pack()

    def hide(self, e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ══════════════════════════════════════════════════════════════
#  GITHUB ENGINE - ALL FEATURES
# ══════════════════════════════════════════════════════════════
class GitHubEngine:
    SKIP = {
        '.git', '__pycache__', 'node_modules', '.DS_Store',
        'Thumbs.db', '.env', '.vscode', '.idea', 'dist', 'build',
        '.pytest_cache', 'venv', '.venv', 'env', '.tox',
        '.mypy_cache', '.eggs'
    }

    def __init__(self, token):
        self.token = token
        self.gh = Github(token, per_page=100)
        self.user = self.gh.get_user()

    @property
    def username(self):
        return self.user.login

    # ── Repository Operations ──

    def list_repos(self):
        result = []
        for r in self.user.get_repos(affiliation="owner", sort="updated"):
            result.append({
                "full_name": r.full_name,
                "name": r.name,
                "private": r.private,
                "description": r.description or "",
                "default_branch": r.default_branch,
                "url": r.html_url
            })
        return result

    def create_repo(self, name, description="", private=False):
        return self.user.create_repo(
            name=name, description=description,
            private=private, auto_init=True
        )

    def delete_repo(self, full_name):
        repo = self.gh.get_repo(full_name)
        repo.delete()

    def get_repo(self, full_name):
        return self.gh.get_repo(full_name)

    # ── Branch Operations ──

    def list_branches(self, full_name):
        repo = self.gh.get_repo(full_name)
        return [b.name for b in repo.get_branches()]

    def create_branch(self, full_name, new_branch, source_branch="main"):
        repo = self.gh.get_repo(full_name)
        source = repo.get_branch(source_branch)
        repo.create_git_ref(
            ref=f"refs/heads/{new_branch}",
            sha=source.commit.sha
        )

    # ── File Operations ──

    def list_remote_files(self, full_name, branch):
        """Get all files in remote repo"""
        repo = self.gh.get_repo(full_name)
        files = []
        try:
            self._recurse_remote(repo, "", branch, files)
        except Exception:
            pass
        return files

    def _recurse_remote(self, repo, path, branch, result):
        try:
            contents = repo.get_contents(path, ref=branch)
            if not isinstance(contents, list):
                contents = [contents]
            for c in contents:
                if c.type == "dir":
                    self._recurse_remote(repo, c.path, branch, result)
                else:
                    result.append({
                        "path": c.path,
                        "sha": c.sha,
                        "size": c.size,
                        "download_url": c.download_url
                    })
        except Exception:
            pass

    def get_file_content(self, full_name, file_path, branch):
        """Get content of a single file"""
        repo = self.gh.get_repo(full_name)
        content = repo.get_contents(file_path, ref=branch)
        return content.decoded_content.decode("utf-8", errors="replace"), content.sha

    def update_single_file(self, full_name, file_path, new_content, 
                           sha, branch, commit_msg):
        """Update a single file in repo"""
        repo = self.gh.get_repo(full_name)
        if isinstance(new_content, str):
            new_content = new_content.encode("utf-8")
        repo.update_file(
            path=file_path,
            message=commit_msg,
            content=new_content,
            sha=sha,
            branch=branch
        )

    def create_single_file(self, full_name, file_path, content, branch, commit_msg):
        """Create a new single file"""
        repo = self.gh.get_repo(full_name)
        if isinstance(content, str):
            content = content.encode("utf-8")
        repo.create_file(
            path=file_path,
            message=commit_msg,
            content=content,
            branch=branch
        )

    def delete_file(self, full_name, file_path, sha, branch, commit_msg):
        """Delete a single file from repo"""
        repo = self.gh.get_repo(full_name)
        repo.delete_file(
            path=file_path,
            message=commit_msg,
            sha=sha,
            branch=branch
        )

    # ── Folder Upload ──

    def should_skip(self, name):
        return name in self.SKIP

    def scan_folder(self, folder_path):
        files = []
        folder_path = os.path.abspath(folder_path)
        for root, dirs, filenames in os.walk(folder_path):
            dirs[:] = [d for d in dirs if not self.should_skip(d)]
            for f in filenames:
                if self.should_skip(f):
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, folder_path).replace("\\", "/")
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    size = 0
                files.append({
                    "full_path": fp,
                    "rel_path": rel,
                    "size": size,
                    "ext": os.path.splitext(f)[1].lower() or ".file"
                })
        return files

    def upload_folder(self, full_name, folder_path, branch="main",
                      commit_msg="Upload files", callback=None):
        repo = self.gh.get_repo(full_name)
        files = self.scan_folder(folder_path)
        total = len(files)

        if callback:
            callback("start", {"total": total})

        # Get existing SHA map
        sha_map = {}
        remote_files = self.list_remote_files(full_name, branch)
        for rf in remote_files:
            sha_map[rf["path"]] = rf["sha"]

        uploaded = 0
        total_bytes = 0
        errors = []
        start_time = time.time()

        for i, f in enumerate(files):
            rel = f["rel_path"]
            try:
                with open(f["full_path"], "rb") as stream:
                    content = stream.read()

                if callback:
                    callback("uploading", {
                        "file": rel, "index": i + 1,
                        "total": total, "size": f["size"]
                    })

                if rel in sha_map:
                    repo.update_file(
                        path=rel,
                        message=f"{commit_msg} - update {rel}",
                        content=content,
                        sha=sha_map[rel],
                        branch=branch
                    )
                else:
                    repo.create_file(
                        path=rel,
                        message=f"{commit_msg} - add {rel}",
                        content=content,
                        branch=branch
                    )

                uploaded += 1
                total_bytes += f["size"]

                elapsed = time.time() - start_time
                speed = total_bytes / elapsed if elapsed > 0 else 0

                if callback:
                    callback("progress", {
                        "file": rel, "uploaded": uploaded,
                        "total": total, "bytes": total_bytes,
                        "speed": speed
                    })

            except Exception as e:
                err_msg = str(e)
                errors.append({"file": rel, "error": err_msg})
                if callback:
                    callback("file_error", {
                        "file": rel, "error": err_msg,
                        "uploaded": uploaded, "total": total
                    })

        elapsed = time.time() - start_time
        if callback:
            callback("done", {
                "uploaded": uploaded, "total": total,
                "bytes": total_bytes, "errors": errors,
                "elapsed": elapsed
            })

        return uploaded, total, errors


# ══════════════════════════════════════════════════════════════
#  FILE ICONS
# ══════════════════════════════════════════════════════════════
ICONS = {
    '.py': '🐍', '.js': '⚡', '.ts': '💎', '.html': '🌐', '.css': '🎨',
    '.json': '📋', '.md': '📝', '.txt': '📄', '.yml': '⚙️', '.yaml': '⚙️',
    '.xml': '📰', '.sql': '🗃️', '.sh': '🖥️', '.bat': '🖥️',
    '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', '.svg': '🎨',
    '.zip': '📦', '.rar': '📦', '.tar': '📦', '.gz': '📦',
    '.java': '☕', '.cpp': '⚙️', '.c': '⚙️', '.go': '🔵', '.rs': '🦀',
    '.php': '🐘', '.dart': '🎯', '.vue': '💚', '.jsx': '⚛️', '.tsx': '⚛️',
    '.rb': '💎', '.swift': '🍎', '.kt': '🟣', '.r': '📊',
    '.toml': '⚙️', '.ini': '⚙️', '.lock': '🔒', '.env': '🔒',
    '.dockerfile': '🐳', '.gitignore': '🚫',
}

def icon_for(ext):
    return ICONS.get(ext.lower(), "📄")

def fmt_size(b):
    if b < 1024: return f"{b} B"
    if b < 1024 * 1024: return f"{b/1024:.1f} KB"
    return f"{b/(1024*1024):.1f} MB"

def fmt_time(s):
    if s < 60: return f"{s:.1f}s"
    return f"{s/60:.1f}min"


# ══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════
class App:

    # GitHub Dark Theme Colors
    C = {
        "bg": "#0d1117",
        "card": "#161b22",
        "input": "#090d13",
        "border": "#30363d",
        "border_hi": "#484f58",
        "text": "#f0f6fc",
        "sub": "#8b949e",
        "muted": "#6e7681",
        "green": "#238636",
        "green2": "#2ea043",
        "blue": "#1f6feb",
        "blue2": "#388bfd",
        "purple": "#8957e5",
        "orange": "#d29922",
        "red": "#f85149",
        "cyan": "#3fb950",
    }

    def __init__(self):
        # State
        self.engine = None
        self.selected_folder = None
        self.scanned_files = []
        self.repos = []
        self.remote_files = []
        self.is_uploading = False
        self.config = self._load_config()

        # Window
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("GitHub Folder Uploader Pro v3.0")
        self.root.geometry("920x920")
        self.root.minsize(800, 700)
        self.root.configure(bg=self.C["bg"])

        self._setup_styles()
        self._build_ui()
        self._load_saved_token()

        self.root.mainloop()

    # ── Config ──

    def _load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception:
            pass

    def _load_saved_token(self):
        t = self.config.get("token", "")
        if t:
            self.token_entry.insert(0, t)

    # ── TTK Styles ──

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TCombobox",
                    fieldbackground=self.C["input"],
                    background=self.C["border"],
                    foreground=self.C["text"],
                    arrowcolor=self.C["text"])
        s.map("TCombobox",
              fieldbackground=[("readonly", self.C["input"])],
              foreground=[("readonly", self.C["text"])])
        s.configure("Treeview",
                    background=self.C["input"],
                    foreground=self.C["text"],
                    fieldbackground=self.C["input"],
                    borderwidth=0,
                    font=("Consolas", 9))
        s.map("Treeview", background=[("selected", self.C["blue"])])
        s.configure("Treeview.Heading",
                    background=self.C["border"],
                    foreground=self.C["text"],
                    font=("Segoe UI", 9, "bold"))

    # ── Helpers ──

    def _card(self, parent, title=""):
        outer = tk.Frame(parent, bg=self.C["border"])
        outer.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(outer, bg=self.C["card"], padx=16, pady=12)
        inner.pack(fill="x", padx=1, pady=1)
        if title:
            tk.Label(inner, text=title, font=("Segoe UI", 10, "bold"),
                    bg=self.C["card"], fg=self.C["text"]).pack(anchor="w", pady=(0, 8))
        return inner, outer

    def _btn(self, parent, text, color, command, **kw):
        b = tk.Button(parent, text=text, bg=color, fg="#ffffff",
                     font=("Segoe UI", 10, "bold"), relief="flat",
                     padx=14, pady=6, cursor="hand2",
                     activebackground=color, activeforeground="#ffffff",
                     command=command, **kw)
        return b

    def _log(self, msg, tag="muted"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] ", "muted")
        self.log_box.insert("end", f"{msg}\n", tag)
        self.log_box.see("end")

    # ══════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════

    def _build_ui(self):
        # Scrollable
        canvas = tk.Canvas(self.root, bg=self.C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        container = tk.Frame(canvas, bg=self.C["bg"])
        container.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.root.bind_all("<MouseWheel>", _scroll)

        # Resize canvas window width
        def _resize(e):
            canvas.itemconfig(canvas.find_all()[0], width=e.width)
        canvas.bind("<Configure>", _resize)

        pad = tk.Frame(container, bg=self.C["bg"], padx=25, pady=18)
        pad.pack(fill="both", expand=True)

        # ── HEADER ──
        hdr = tk.Frame(pad, bg=self.C["bg"])
        hdr.pack(fill="x", pady=(0, 18))

        tk.Label(hdr, text="🚀 GitHub Folder Uploader",
                font=("Segoe UI", 20, "bold"),
                bg=self.C["bg"], fg="#ffffff").pack(side="left")

        badge_f = tk.Frame(hdr, bg=self.C["bg"])
        badge_f.pack(side="right")
        tk.Label(badge_f, text=" v3.0 FULL ", bg=self.C["purple"],
                fg="#fff", font=("Segoe UI", 8, "bold"),
                padx=8, pady=2).pack()

        tk.Label(pad, text="Upload • Edit • Delete • Create Repo • Manage Branch • Drag & Drop",
                font=("Segoe UI", 10), bg=self.C["bg"],
                fg=self.C["sub"]).pack(anchor="w", pady=(0, 15))

        # ── 1. AUTH CARD ──
        auth, _ = self._card(pad, "🔑  STEP 1: CONNECT GITHUB")

        auth_row = tk.Frame(auth, bg=self.C["card"])
        auth_row.pack(fill="x")

        # Token Input
        inp_wrap = tk.Frame(auth_row, bg=self.C["border"])
        inp_wrap.pack(side="left", fill="x", expand=True, padx=(0, 10))
        inp_inner = tk.Frame(inp_wrap, bg=self.C["input"])
        inp_inner.pack(fill="x", padx=1, pady=1)

        tk.Label(inp_inner, text="🔑", bg=self.C["input"],
                font=("Segoe UI", 11)).pack(side="left", padx=(8, 4))

        self.token_entry = tk.Entry(inp_inner, show="•", font=("Consolas", 11),
                                   bg=self.C["input"], fg=self.C["text"],
                                   insertbackground=self.C["text"],
                                   relief="flat", bd=7)
        self.token_entry.pack(side="left", fill="x", expand=True)

        self.show_pw = False
        eye = tk.Label(inp_inner, text="👁", bg=self.C["input"],
                      font=("Segoe UI", 11), cursor="hand2")
        eye.pack(side="right", padx=8)
        eye.bind("<Button-1>", self._toggle_pw)

        self.btn_conn = self._btn(auth_row, "Connect", self.C["green"],
                                 self.do_connect)
        self.btn_conn.pack(side="right")

        # Status + help
        status_row = tk.Frame(auth, bg=self.C["card"])
        status_row.pack(fill="x", pady=(8, 0))

        self.lbl_status = tk.Label(status_row, text="⚪ Belum terhubung",
                                  font=("Segoe UI", 9), bg=self.C["card"],
                                  fg=self.C["muted"])
        self.lbl_status.pack(side="left")

        link = tk.Label(status_row, text="Buat token baru →",
                       font=("Segoe UI", 9, "underline"),
                       bg=self.C["card"], fg=self.C["blue"], cursor="hand2")
        link.pack(side="right")
        link.bind("<Button-1>", lambda e: webbrowser.open(
            "https://github.com/settings/tokens/new?scopes=repo,delete_repo&description=UploaderProV3"))

        # ── 2. DROP ZONE ──
        self.drop_outer = tk.Frame(pad, bg=self.C["border"])
        self.drop_outer.pack(fill="x", pady=(0, 12))

        self.drop_box = tk.Frame(self.drop_outer, bg=self.C["card"],
                                cursor="hand2")
        self.drop_box.pack(fill="x", padx=2, pady=2)

        drop_pad = tk.Frame(self.drop_box, bg=self.C["card"], padx=20, pady=28)
        drop_pad.pack(fill="x")

        self.lbl_drop_icon = tk.Label(drop_pad, text="📂",
                                     font=("Segoe UI", 40),
                                     bg=self.C["card"])
        self.lbl_drop_icon.pack()

        self.lbl_drop_title = tk.Label(drop_pad, text="STEP 2: Drop Folder Disini",
                                      font=("Segoe UI", 14, "bold"),
                                      bg=self.C["card"], fg=self.C["text"])
        self.lbl_drop_title.pack(pady=(8, 3))

        self.lbl_drop_info = tk.Label(drop_pad,
                                     text="Klik atau drag & drop folder yang ingin di-upload",
                                     font=("Segoe UI", 10),
                                     bg=self.C["card"], fg=self.C["sub"])
        self.lbl_drop_info.pack()

        tk.Label(drop_pad,
                text="Auto-skip: .git, node_modules, __pycache__, venv, dist, build, dll",
                font=("Segoe UI", 8), bg=self.C["card"],
                fg=self.C["muted"]).pack(pady=(8, 0))

        self.badge_frame = tk.Frame(drop_pad, bg=self.C["card"])

        # Browse button
        self._btn(drop_pad, "📁 Browse Folder", self.C["border"],
                 self.browse_folder).pack(pady=(12, 0))

        # Click to browse
        for w in [self.drop_box, drop_pad, self.lbl_drop_icon,
                  self.lbl_drop_title, self.lbl_drop_info]:
            w.bind("<Button-1>", lambda e: self.browse_folder())

        # DnD
        if DND_AVAILABLE:
            self.drop_box.drop_target_register(DND_FILES)
            self.drop_box.dnd_bind('<<DropEnter>>', self._dnd_enter)
            self.drop_box.dnd_bind('<<DropLeave>>', self._dnd_leave)
            self.drop_box.dnd_bind('<<Drop>>', self._dnd_drop)

        # ── 3. REPO CARD ──
        repo_card, _ = self._card(pad, "📦  STEP 3: PILIH REPOSITORY")

        # Select existing
        tk.Label(repo_card, text="Pilih Repository:",
                font=("Segoe UI", 9), bg=self.C["card"],
                fg=self.C["sub"]).pack(anchor="w", pady=(0, 4))

        sel_row = tk.Frame(repo_card, bg=self.C["card"])
        sel_row.pack(fill="x", pady=(0, 8))

        self.repo_var = tk.StringVar()
        self.repo_combo = ttk.Combobox(sel_row, textvariable=self.repo_var,
                                       state="readonly", font=("Segoe UI", 10))
        self.repo_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.repo_combo.bind("<<ComboboxSelected>>", self._on_repo_selected)

        self._btn(sel_row, "🔄", self.C["border"], self.do_refresh_repos).pack(side="right")

        # Repo info label
        self.lbl_repo_info = tk.Label(repo_card, text="",
                                     font=("Segoe UI", 9),
                                     bg=self.C["card"], fg=self.C["sub"])
        self.lbl_repo_info.pack(anchor="w", pady=(0, 5))

        # Divider
        tk.Frame(repo_card, bg=self.C["border"], height=1).pack(fill="x", pady=8)

        # Create new repo
        tk.Label(repo_card, text="➕ Atau buat Repository baru:",
                font=("Segoe UI", 9), bg=self.C["card"],
                fg=self.C["sub"]).pack(anchor="w", pady=(0, 4))

        cr_row = tk.Frame(repo_card, bg=self.C["card"])
        cr_row.pack(fill="x", pady=(0, 5))

        self.new_repo_entry = tk.Entry(cr_row, font=("Segoe UI", 10),
                                      bg=self.C["input"], fg=self.C["text"],
                                      insertbackground=self.C["text"],
                                      relief="flat", bd=6)
        self.new_repo_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.priv_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cr_row, text="🔒Private", variable=self.priv_var,
                      bg=self.C["card"], fg=self.C["text"],
                      selectcolor=self.C["input"],
                      activebackground=self.C["card"],
                      font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))

        self._btn(cr_row, "➕ Create", self.C["blue"],
                 self.do_create_repo).pack(side="right")

        # Branch & Commit
        tk.Frame(repo_card, bg=self.C["border"], height=1).pack(fill="x", pady=8)

        opt_row = tk.Frame(repo_card, bg=self.C["card"])
        opt_row.pack(fill="x")

        # Branch
        bf = tk.Frame(opt_row, bg=self.C["card"])
        bf.pack(side="left", padx=(0, 10))
        tk.Label(bf, text="Branch:", font=("Segoe UI", 9),
                bg=self.C["card"], fg=self.C["sub"]).pack(anchor="w")
        self.branch_combo = ttk.Combobox(bf, font=("Segoe UI", 10),
                                         width=14)
        self.branch_combo.pack(pady=(2, 0))
        self.branch_combo.set("main")

        # New branch button
        self._btn(opt_row, "🌿 New Branch", self.C["border"],
                 self.do_create_branch).pack(side="left", padx=(0, 12), pady=(15, 0))

        # Commit message
        cf = tk.Frame(opt_row, bg=self.C["card"])
        cf.pack(side="left", fill="x", expand=True)
        tk.Label(cf, text="Commit Message:", font=("Segoe UI", 9),
                bg=self.C["card"], fg=self.C["sub"]).pack(anchor="w")
        self.commit_entry = tk.Entry(cf, font=("Segoe UI", 10),
                                    bg=self.C["input"], fg=self.C["text"],
                                    insertbackground=self.C["text"],
                                    relief="flat", bd=5)
        self.commit_entry.pack(fill="x", pady=(2, 0))
        self.commit_entry.insert(0, "Upload via GitHub Uploader Pro 🚀")

        # ── 4. UPLOAD BUTTON ──
        self.btn_upload = tk.Button(
            pad, text="🚀  UPLOAD FOLDER TO GITHUB",
            font=("Segoe UI", 13, "bold"), bg=self.C["border"],
            fg=self.C["muted"], relief="flat", pady=14,
            cursor="arrow", state="disabled",
            command=self.do_upload
        )
        self.btn_upload.pack(fill="x", pady=(5, 12))

        # ── 5. REMOTE FILES MANAGER ──
        mgr_card, self.mgr_outer = self._card(pad, "🗂️  MANAGE REMOTE FILES (Edit / Delete)")
        self.mgr_outer.pack_forget()

        mgr_btn_row = tk.Frame(mgr_card, bg=self.C["card"])
        mgr_btn_row.pack(fill="x", pady=(0, 8))

        self._btn(mgr_btn_row, "🔄 Load Files", self.C["border"],
                 self.do_load_remote).pack(side="left", padx=(0, 5))
        self._btn(mgr_btn_row, "📝 Edit Selected", self.C["blue"],
                 self.do_edit_file).pack(side="left", padx=(0, 5))
        self._btn(mgr_btn_row, "🗑️ Delete Selected", self.C["red"],
                 self.do_delete_file).pack(side="left", padx=(0, 5))
        self._btn(mgr_btn_row, "📄 Create New File", self.C["green"],
                 self.do_create_file).pack(side="left")

        # Treeview for remote files
        tree_frame = tk.Frame(mgr_card, bg=self.C["card"])
        tree_frame.pack(fill="both", expand=True)

        self.file_tree = ttk.Treeview(tree_frame, columns=("path", "size"),
                                      show="headings", height=6,
                                      selectmode="browse")
        self.file_tree.heading("path", text="📄 File Path")
        self.file_tree.heading("size", text="💾 Size")
        self.file_tree.column("path", width=500)
        self.file_tree.column("size", width=100, anchor="e")

        tree_scroll = tk.Scrollbar(tree_frame, orient="vertical",
                                  command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        self.file_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # ── 6. PROGRESS ──
        self.prog_card, self.prog_outer = self._card(pad, "📊  UPLOAD PROGRESS")
        self.prog_outer.pack_forget()

        stat_row = tk.Frame(self.prog_card, bg=self.C["card"])
        stat_row.pack(fill="x", pady=(0, 8))

        self.stat_up = self._stat_box(stat_row, "Uploaded", "0", self.C["green"])
        self.stat_tot = self._stat_box(stat_row, "Total", "0", self.C["blue"])
        self.stat_sz = self._stat_box(stat_row, "Data", "0 B", self.C["purple"])
        self.stat_spd = self._stat_box(stat_row, "Speed", "—", self.C["orange"])

        # Custom progress bar
        self.prog_canvas = tk.Canvas(self.prog_card, height=10,
                                    bg=self.C["input"], highlightthickness=0)
        self.prog_canvas.pack(fill="x", pady=5)
        self.prog_rect = self.prog_canvas.create_rectangle(0, 0, 0, 10,
                                                          fill=self.C["green"],
                                                          outline="")

        self.lbl_pct = tk.Label(self.prog_card, text="0%",
                               font=("Segoe UI", 11, "bold"),
                               bg=self.C["card"], fg=self.C["text"])
        self.lbl_pct.pack()

        self.lbl_curfile = tk.Label(self.prog_card, text="",
                                   font=("Consolas", 8),
                                   bg=self.C["card"], fg=self.C["muted"],
                                   wraplength=700)
        self.lbl_curfile.pack()

        # ── 7. LOG ──
        log_card, _ = self._card(pad, "📋  ACTIVITY LOG")

        log_wrap = tk.Frame(log_card, bg=self.C["card"])
        log_wrap.pack(fill="both", expand=True)

        self.log_box = tk.Text(log_wrap, height=8, font=("Consolas", 9),
                              bg=self.C["input"], fg=self.C["text"],
                              insertbackground=self.C["text"],
                              relief="flat", bd=8, wrap="word")

        log_scr = tk.Scrollbar(log_wrap, orient="vertical",
                              command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scr.set)
        log_scr.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True)

        # Log tags
        for tag, color in [("green", self.C["green"]), ("blue", self.C["blue"]),
                           ("red", self.C["red"]), ("orange", self.C["orange"]),
                           ("muted", self.C["muted"]), ("purple", self.C["purple"]),
                           ("bold", self.C["text"])]:
            self.log_box.tag_config(tag, foreground=color)
        self.log_box.tag_config("bold", font=("Consolas", 9, "bold"))

        self._log("🚀 GitHub Uploader Pro v3.0 - Full Feature Edition", "blue")
        self._log("   Upload • Edit • Delete • Create Repo • Branch Management", "muted")
        if not DND_AVAILABLE:
            self._log("💡 Untuk drag & drop: pip install tkinterdnd2", "orange")

        # ── 8. FOOTER ──
        tk.Label(pad, text="Made with ❤️ • GitHub Folder Uploader Pro v3.0",
                font=("Segoe UI", 8), bg=self.C["bg"],
                fg=self.C["muted"]).pack(pady=(8, 0))

    def _stat_box(self, parent, title, val, color):
        f = tk.Frame(parent, bg=self.C["input"], padx=8, pady=6)
        f.pack(side="left", fill="x", expand=True, padx=3)
        v = tk.Label(f, text=val, font=("Segoe UI", 13, "bold"),
                    bg=self.C["input"], fg=color)
        v.pack()
        tk.Label(f, text=title, font=("Segoe UI", 8),
                bg=self.C["input"], fg=self.C["muted"]).pack()
        return v

    # ══════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════

    def _toggle_pw(self, e=None):
        self.show_pw = not self.show_pw
        self.token_entry.config(show="" if self.show_pw else "•")

    def _validate_ready(self):
        ok = (self.engine is not None
              and self.selected_folder is not None
              and bool(self.repo_var.get())
              and not self.is_uploading)
        if ok:
            self.btn_upload.config(state="normal", bg=self.C["green"],
                                  fg="#fff", cursor="hand2")
        else:
            self.btn_upload.config(state="disabled", bg=self.C["border"],
                                  fg=self.C["muted"], cursor="arrow")

    def _get_repo_fullname(self):
        """Extract clean repo full_name from combo display"""
        display = self.repo_var.get()
        if not display:
            return None
        # Remove emoji prefix like "🔒 " or "🌐 "
        for prefix in ["🔒 ", "🌐 ", "📂 "]:
            if display.startswith(prefix):
                display = display[len(prefix):]
                break
        # Also try splitting by space and taking last part
        parts = display.strip().split()
        if parts:
            return parts[-1]
        return display.strip()

    # ── CONNECT ──

    def do_connect(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("⚠️", "Masukkan GitHub Access Token!")
            return

        self.btn_conn.config(text="⏳...", state="disabled")
        self.lbl_status.config(text="🟡 Menghubungkan...", fg=self.C["orange"])
        self.root.update()

        def _work():
            try:
                engine = GitHubEngine(token)
                name = engine.username
                self.root.after(0, lambda: self._connected(engine, token, name))
            except Exception as e:
                self.root.after(0, lambda: self._connect_fail(str(e)))

        threading.Thread(target=_work, daemon=True).start()

    def _connected(self, engine, token, user):
        self.engine = engine
        self.config["token"] = token
        self._save_config()

        self.btn_conn.config(text="✅ Connected", state="normal",
                            bg=self.C["green"])
        self.lbl_status.config(text=f"🟢 Terhubung: @{user}", fg=self.C["cyan"])
        self._log(f"✅ Terhubung ke GitHub sebagai @{user}", "green")

        # Show file manager
        self.mgr_outer.pack(fill="x", pady=(0, 12))

        self.do_refresh_repos()
        self._validate_ready()

    def _connect_fail(self, err):
        self.btn_conn.config(text="Connect", state="normal")
        self.lbl_status.config(text="🔴 Gagal!", fg=self.C["red"])
        self._log(f"❌ Koneksi gagal: {err}", "red")
        messagebox.showerror("Error", f"Gagal konek:\n{err}")

    # ── REPOS ──

    def do_refresh_repos(self):
        if not self.engine:
            return
        self._log("🔄 Memuat daftar repository...", "blue")

        def _work():
            try:
                repos = self.engine.list_repos()
                self.root.after(0, lambda: self._repos_loaded(repos))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Error: {e}", "red"))

        threading.Thread(target=_work, daemon=True).start()

    def _repos_loaded(self, repos):
        self.repos = repos
        display = []
        for r in repos:
            icon = "🔒" if r["private"] else "🌐"
            display.append(f"{icon} {r['full_name']}")

        self.repo_combo["values"] = display
        if display:
            self.repo_combo.current(0)
            self._on_repo_selected()

        self._log(f"📦 {len(repos)} repository ditemukan", "green")
        self._validate_ready()

    def _on_repo_selected(self, e=None):
        full_name = self._get_repo_fullname()
        if not full_name:
            return

        # Find repo info
        info = None
        for r in self.repos:
            if r["full_name"] == full_name:
                info = r
                break

        if info:
            self.lbl_repo_info.config(
                text=f"📌 {info['full_name']} • "
                     f"{'🔒 Private' if info['private'] else '🌐 Public'} • "
                     f"Branch default: {info['default_branch']}"
            )
            self.branch_combo.set(info["default_branch"])

        # Load branches in background
        def _load_branches():
            try:
                branches = self.engine.list_branches(full_name)
                self.root.after(0, lambda: self.branch_combo.config(values=branches))
            except Exception:
                pass

        threading.Thread(target=_load_branches, daemon=True).start()
        self._validate_ready()

    # ── CREATE REPO ──

    def do_create_repo(self):
        if not self.engine:
            messagebox.showwarning("⚠️", "Hubungkan GitHub dulu!")
            return

        name = self.new_repo_entry.get().strip()
        if not name:
            messagebox.showwarning("⚠️", "Masukkan nama repo!")
            return

        self._log(f"📦 Membuat repository '{name}'...", "blue")

        def _work():
            try:
                repo = self.engine.create_repo(name, private=self.priv_var.get())
                self.root.after(0, lambda: self._repo_created(repo))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Gagal: {e}", "red"))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=_work, daemon=True).start()

    def _repo_created(self, repo):
        self._log(f"✅ Repository dibuat: {repo.full_name}", "green")
        self.new_repo_entry.delete(0, "end")
        self.do_refresh_repos()

    # ── CREATE BRANCH ──

    def do_create_branch(self):
        if not self.engine:
            return

        full_name = self._get_repo_fullname()
        if not full_name:
            messagebox.showwarning("⚠️", "Pilih repository dulu!")
            return

        new_name = simpledialog.askstring(
            "🌿 New Branch",
            "Nama branch baru:",
            parent=self.root
        )
        if not new_name:
            return

        source = self.branch_combo.get() or "main"
        self._log(f"🌿 Membuat branch '{new_name}' dari '{source}'...", "blue")

        def _work():
            try:
                self.engine.create_branch(full_name, new_name, source)
                self.root.after(0, lambda: self._branch_created(new_name, full_name))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Gagal: {e}", "red"))

        threading.Thread(target=_work, daemon=True).start()

    def _branch_created(self, name, full_name):
        self._log(f"✅ Branch '{name}' berhasil dibuat!", "green")
        # Refresh branches
        try:
            branches = self.engine.list_branches(full_name)
            self.branch_combo.config(values=branches)
            self.branch_combo.set(name)
        except Exception:
            pass

    # ── FOLDER SELECTION ──

    def browse_folder(self):
        f = filedialog.askdirectory(title="Pilih Folder untuk Upload")
        if f:
            self.set_folder(f)

    def set_folder(self, path):
        path = path.strip("{}\"'")
        if not os.path.isdir(path):
            return

        self.selected_folder = path
        name = os.path.basename(path)

        if self.engine:
            self.scanned_files = self.engine.scan_folder(path)
        else:
            self.scanned_files = []
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
                for f in files:
                    fp = os.path.join(root, f)
                    self.scanned_files.append({
                        "full_path": fp,
                        "rel_path": os.path.relpath(fp, path).replace("\\", "/"),
                        "size": os.path.getsize(fp),
                        "ext": os.path.splitext(f)[1].lower() or ".file"
                    })

        total_size = sum(f["size"] for f in self.scanned_files)

        self.drop_outer.config(bg=self.C["green"])
        self.lbl_drop_icon.config(text="✅", fg=self.C["green"])
        self.lbl_drop_title.config(text=f"📂 {name}")
        self.lbl_drop_info.config(
            text=f"📍 {path}\n"
                 f"📄 {len(self.scanned_files)} files • 💾 {fmt_size(total_size)}"
        )

        # Extension badges
        self.badge_frame.pack(fill="x", pady=(10, 0))
        for w in self.badge_frame.winfo_children():
            w.destroy()

        ext_map = {}
        for f in self.scanned_files:
            ext_map[f["ext"]] = ext_map.get(f["ext"], 0) + 1

        row = tk.Frame(self.badge_frame, bg=self.C["card"])
        row.pack()
        for ext, cnt in sorted(ext_map.items(), key=lambda x: -x[1])[:8]:
            tk.Label(row, text=f" {icon_for(ext)} {ext} ({cnt}) ",
                    bg=self.C["input"], fg=self.C["sub"],
                    font=("Segoe UI", 8), padx=4, pady=1).pack(side="left", padx=2)

        self._log(f"📂 Folder: {name} ({len(self.scanned_files)} files, {fmt_size(total_size)})", "green")
        self._validate_ready()

    # DnD Handlers
    def _dnd_enter(self, e):
        self.drop_outer.config(bg=self.C["blue"])
        self.lbl_drop_title.config(text="⬇️ Drop sekarang!", fg=self.C["blue"])

    def _dnd_leave(self, e):
        self.drop_outer.config(
            bg=self.C["green"] if self.selected_folder else self.C["border"])
        self.lbl_drop_title.config(fg=self.C["text"])

    def _dnd_drop(self, e):
        p = e.data.strip("{}\"")
        if os.path.isdir(p):
            self.set_folder(p)
        elif os.path.isfile(p):
            self.set_folder(os.path.dirname(p))

    # ── UPLOAD ──

    def do_upload(self):
        if not self.engine or not self.selected_folder:
            return

        full_name = self._get_repo_fullname()
        if not full_name:
            messagebox.showwarning("⚠️", "Pilih repository!")
            return

        n = len(self.scanned_files)
        branch = self.branch_combo.get() or "main"
        commit = self.commit_entry.get().strip() or "Upload files"

        if not messagebox.askyesno("🚀 Konfirmasi Upload",
                                   f"Upload {n} file ke:\n"
                                   f"📦 {full_name}\n"
                                   f"🌿 Branch: {branch}\n\n"
                                   f"Lanjutkan?"):
            return

        self.is_uploading = True
        self.btn_upload.config(state="disabled", text="⏳ UPLOADING...",
                             bg=self.C["orange"])

        # Show progress
        self.prog_outer.pack(fill="x", pady=(0, 12))
        self.stat_up.config(text="0")
        self.stat_tot.config(text=str(n))
        self.stat_sz.config(text="0 B")
        self.stat_spd.config(text="—")
        self.lbl_pct.config(text="0%")
        self.prog_canvas.coords(self.prog_rect, 0, 0, 0, 10)
        self.lbl_curfile.config(text="Memulai...")

        self._log(f"\n{'═'*50}", "bold")
        self._log(f"🚀 Upload ke {full_name} ({branch}) dimulai!", "bold")
        self._log(f"{'═'*50}", "bold")

        def _work():
            def cb(ev, data):
                self.root.after(0, lambda: self._upload_event(ev, data, full_name))

            try:
                self.engine.upload_folder(full_name, self.selected_folder,
                                         branch, commit, cb)
            except Exception as e:
                self.root.after(0, lambda: self._upload_event(
                    "fatal", {"error": str(e)}, full_name))

        threading.Thread(target=_work, daemon=True).start()

    def _upload_event(self, ev, data, repo):
        if ev == "start":
            self.stat_tot.config(text=str(data["total"]))

        elif ev == "uploading":
            f = data["file"]
            ic = icon_for(os.path.splitext(f)[1])
            self.lbl_curfile.config(text=f"{ic} {f}")

        elif ev == "progress":
            up = data["uploaded"]
            tot = data["total"]
            b = data["bytes"]
            spd = data.get("speed", 0)
            pct = int(up / tot * 100) if tot else 0

            self.stat_up.config(text=str(up))
            self.stat_sz.config(text=fmt_size(b))
            self.stat_spd.config(text=f"{fmt_size(int(spd))}/s")
            self.lbl_pct.config(text=f"{pct}%")

            w = self.prog_canvas.winfo_width()
            self.prog_canvas.coords(self.prog_rect, 0, 0,
                                   int(w * pct / 100), 10)

            f = data["file"]
            ic = icon_for(os.path.splitext(f)[1])
            self._log(f"  ✅ {ic} {f} ({up}/{tot})", "green")

        elif ev == "file_error":
            self._log(f"  ❌ {data['file']}: {data['error']}", "red")

        elif ev == "done":
            up = data["uploaded"]
            tot = data["total"]
            errs = data["errors"]
            elapsed = data.get("elapsed", 0)

            w = self.prog_canvas.winfo_width()
            self.prog_canvas.coords(self.prog_rect, 0, 0, w, 10)
            self.lbl_pct.config(text="100% ✅")
            self.lbl_curfile.config(text="✨ Selesai!")
            self.stat_spd.config(text=fmt_time(elapsed))

            self.is_uploading = False
            self._validate_ready()
            self.btn_upload.config(text="🚀  UPLOAD FOLDER TO GITHUB")

            self._log(f"\n{'═'*50}", "bold")
            self._log(f"🎉 Selesai! {up}/{tot} file terupload", "green")
            self._log(f"💾 Total: {fmt_size(data['bytes'])} dalam {fmt_time(elapsed)}", "blue")
            if errs:
                self._log(f"⚠️ {len(errs)} error", "orange")
            self._log(f"{'═'*50}", "bold")

            if messagebox.askyesno("🎉 Upload Berhasil!",
                                   f"✅ {up}/{tot} file terupload!\n"
                                   f"💾 {fmt_size(data['bytes'])} dalam {fmt_time(elapsed)}\n\n"
                                   f"Buka di browser?"):
                webbrowser.open(f"https://github.com/{repo}")

        elif ev == "fatal":
            self.is_uploading = False
            self._validate_ready()
            self.btn_upload.config(text="🚀  UPLOAD FOLDER TO GITHUB")
            self._log(f"💥 Fatal: {data['error']}", "red")
            messagebox.showerror("Error", data["error"])

    # ── REMOTE FILE MANAGER ──

    def do_load_remote(self):
        full_name = self._get_repo_fullname()
        if not full_name or not self.engine:
            messagebox.showwarning("⚠️", "Pilih repository dan connect dulu!")
            return

        branch = self.branch_combo.get() or "main"
        self._log(f"🔄 Memuat file remote dari {full_name}...", "blue")

        def _work():
            try:
                files = self.engine.list_remote_files(full_name, branch)
                self.root.after(0, lambda: self._remote_loaded(files))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Error: {e}", "red"))

        threading.Thread(target=_work, daemon=True).start()

    def _remote_loaded(self, files):
        self.remote_files = files

        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        for f in files:
            ic = icon_for(os.path.splitext(f["path"])[1])
            self.file_tree.insert("", "end", values=(
                f"{ic}  {f['path']}",
                fmt_size(f["size"])
            ))

        self._log(f"📄 {len(files)} file ditemukan di remote", "green")

    def _get_selected_remote_file(self):
        sel = self.file_tree.selection()
        if not sel:
            messagebox.showwarning("⚠️", "Pilih file di daftar terlebih dahulu!")
            return None, None

        values = self.file_tree.item(sel[0], "values")
        # Extract path (remove icon)
        display_path = values[0]
        # Remove leading emoji + spaces
        clean_path = display_path
        for ic in ICONS.values():
            if clean_path.startswith(ic):
                clean_path = clean_path[len(ic):].strip()
                break
        if clean_path.startswith("📄"):
            clean_path = clean_path[2:].strip()

        # Find matching remote file
        for rf in self.remote_files:
            if rf["path"] == clean_path:
                return rf["path"], rf["sha"]

        # Fallback: try matching by end of string
        for rf in self.remote_files:
            if clean_path.endswith(rf["path"]) or rf["path"].endswith(clean_path.strip()):
                return rf["path"], rf["sha"]

        messagebox.showerror("Error", f"File tidak ditemukan: {clean_path}")
        return None, None

    def do_edit_file(self):
        full_name = self._get_repo_fullname()
        if not full_name or not self.engine:
            return

        file_path, sha = self._get_selected_remote_file()
        if not file_path:
            return

        branch = self.branch_combo.get() or "main"
        self._log(f"📝 Loading {file_path} for editing...", "blue")

        def _work():
            try:
                content, current_sha = self.engine.get_file_content(
                    full_name, file_path, branch)
                self.root.after(0, lambda: self._open_editor(
                    full_name, file_path, content, current_sha, branch))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Error: {e}", "red"))
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=_work, daemon=True).start()

    def _open_editor(self, full_name, file_path, content, sha, branch):
        """Open file editor window"""
        editor = tk.Toplevel(self.root)
        editor.title(f"📝 Edit: {file_path}")
        editor.geometry("750x550")
        editor.configure(bg=self.C["bg"])
        editor.transient(self.root)
        editor.grab_set()

        # Header
        hdr = tk.Frame(editor, bg=self.C["card"], padx=15, pady=10)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"📝 Editing: {file_path}",
                font=("Segoe UI", 11, "bold"),
                bg=self.C["card"], fg=self.C["text"]).pack(side="left")

        tk.Label(hdr, text=f"📦 {full_name} • 🌿 {branch}",
                font=("Segoe UI", 9),
                bg=self.C["card"], fg=self.C["sub"]).pack(side="right")

        # Text editor
        text_frame = tk.Frame(editor, bg=self.C["bg"])
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, font=("Consolas", 11),
                             bg=self.C["input"], fg=self.C["text"],
                             insertbackground=self.C["text"],
                             relief="flat", bd=8, wrap="none",
                             undo=True)

        sx = tk.Scrollbar(text_frame, orient="horizontal",
                         command=text_widget.xview)
        sy = tk.Scrollbar(text_frame, orient="vertical",
                         command=text_widget.yview)
        text_widget.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)

        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        text_widget.pack(fill="both", expand=True)

        text_widget.insert("1.0", content)

        # Commit message
        bottom = tk.Frame(editor, bg=self.C["card"], padx=15, pady=10)
        bottom.pack(fill="x")

        tk.Label(bottom, text="Commit:", font=("Segoe UI", 9),
                bg=self.C["card"], fg=self.C["sub"]).pack(side="left")

        commit_e = tk.Entry(bottom, font=("Segoe UI", 10),
                           bg=self.C["input"], fg=self.C["text"],
                           insertbackground=self.C["text"],
                           relief="flat", bd=5)
        commit_e.pack(side="left", fill="x", expand=True, padx=8)
        commit_e.insert(0, f"Edit {file_path} via Uploader Pro")

        def _save():
            new_content = text_widget.get("1.0", "end-1c")
            msg = commit_e.get().strip() or f"Update {file_path}"

            def _work():
                try:
                    self.engine.update_single_file(
                        full_name, file_path, new_content,
                        sha, branch, msg
                    )
                    self.root.after(0, lambda: self._log(
                        f"✅ File updated: {file_path}", "green"))
                    self.root.after(0, editor.destroy)
                    self.root.after(100, self.do_load_remote)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

            threading.Thread(target=_work, daemon=True).start()

        save_btn = self._btn(bottom, "💾 Save & Push", self.C["green"], _save)
        save_btn.pack(side="right")

    def do_delete_file(self):
        full_name = self._get_repo_fullname()
        if not full_name or not self.engine:
            return

        file_path, sha = self._get_selected_remote_file()
        if not file_path:
            return

        if not messagebox.askyesno("🗑️ Hapus File?",
                                   f"Hapus file:\n{file_path}\n\n"
                                   f"dari {full_name}?\n\n"
                                   f"Aksi ini tidak bisa dibatalkan!"):
            return

        branch = self.branch_combo.get() or "main"
        self._log(f"🗑️ Menghapus {file_path}...", "orange")

        def _work():
            try:
                self.engine.delete_file(
                    full_name, file_path, sha, branch,
                    f"Delete {file_path} via Uploader Pro"
                )
                self.root.after(0, lambda: self._log(
                    f"✅ File dihapus: {file_path}", "green"))
                self.root.after(0, self.do_load_remote)
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Error: {e}", "red"))

        threading.Thread(target=_work, daemon=True).start()

    def do_create_file(self):
        full_name = self._get_repo_fullname()
        if not full_name or not self.engine:
            messagebox.showwarning("⚠️", "Connect dan pilih repo dulu!")
            return

        branch = self.branch_combo.get() or "main"

        # Dialog for file path
        file_path = simpledialog.askstring(
            "📄 Create New File",
            "Path file baru (contoh: src/hello.py):",
            parent=self.root
        )
        if not file_path:
            return

        # Open editor with empty content
        self._open_creator(full_name, file_path, branch)

    def _open_creator(self, full_name, file_path, branch):
        editor = tk.Toplevel(self.root)
        editor.title(f"📄 Create: {file_path}")
        editor.geometry("750x550")
        editor.configure(bg=self.C["bg"])
        editor.transient(self.root)
        editor.grab_set()

        hdr = tk.Frame(editor, bg=self.C["card"], padx=15, pady=10)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"📄 New File: {file_path}",
                font=("Segoe UI", 11, "bold"),
                bg=self.C["card"], fg=self.C["text"]).pack(side="left")

        text_frame = tk.Frame(editor, bg=self.C["bg"])
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, font=("Consolas", 11),
                             bg=self.C["input"], fg=self.C["text"],
                             insertbackground=self.C["text"],
                             relief="flat", bd=8, wrap="none", undo=True)

        sy = tk.Scrollbar(text_frame, orient="vertical",
                         command=text_widget.yview)
        text_widget.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        text_widget.pack(fill="both", expand=True)

        bottom = tk.Frame(editor, bg=self.C["card"], padx=15, pady=10)
        bottom.pack(fill="x")

        commit_e = tk.Entry(bottom, font=("Segoe UI", 10),
                           bg=self.C["input"], fg=self.C["text"],
                           insertbackground=self.C["text"],
                           relief="flat", bd=5)
        commit_e.pack(side="left", fill="x", expand=True, padx=(0, 8))
        commit_e.insert(0, f"Create {file_path}")

        def _create():
            content = text_widget.get("1.0", "end-1c")
            msg = commit_e.get().strip() or f"Create {file_path}"

            def _work():
                try:
                    self.engine.create_single_file(
                        full_name, file_path, content, branch, msg
                    )
                    self.root.after(0, lambda: self._log(
                        f"✅ File dibuat: {file_path}", "green"))
                    self.root.after(0, editor.destroy)
                    self.root.after(100, self.do_load_remote)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

            threading.Thread(target=_work, daemon=True).start()

        self._btn(bottom, "📄 Create & Push", self.C["green"], _create).pack(side="right")


# ══════════════════════════════════════════════════════════════
#  LAUNCH
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════╗
    ║  🚀 GitHub Folder Uploader Pro v3.0              ║
    ║  Full Feature Edition                            ║
    ║  Upload • Edit • Delete • Create • Branch Mgmt   ║
    ╚══════════════════════════════════════════════════╝
    """)
    App()