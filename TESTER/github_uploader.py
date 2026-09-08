#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  🚀 GITHUB UPLOADER PRO - ULTRA EDITION v4.1                   ║
║  + Move File Feature • Rename • Drag to Folder                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import threading
import webbrowser
import time
import zipfile
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ── Auto-install ──
def _install(pkg):
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    from github import Github, GithubException
except ImportError:
    print("📦 Installing PyGithub...")
    _install("PyGithub")
    from github import Github, GithubException

DND_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    pass

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".github_uploader_v4.json")

# ══════════════════════════════════════════════════════════════
#  CONSTANTS & HELPERS
# ══════════════════════════════════════════════════════════════

SKIP_DIRS = {'.git','__pycache__','node_modules','.DS_Store','Thumbs.db',
             '.vscode','.idea','dist','build','.pytest_cache','venv',
             '.venv','env','.tox','.mypy_cache','.eggs'}

FILE_ICONS = {
    '.py':'🐍','.js':'⚡','.ts':'💎','.html':'🌐','.css':'🎨','.scss':'🎨',
    '.json':'📋','.md':'📝','.txt':'📄','.yml':'⚙️','.yaml':'⚙️','.xml':'📰',
    '.sql':'🗃️','.sh':'🖥️','.bat':'🖥️','.ps1':'🖥️',
    '.png':'🖼️','.jpg':'🖼️','.jpeg':'🖼️','.gif':'🖼️','.svg':'🎨',
    '.webp':'🖼️','.ico':'🖼️','.bmp':'🖼️','.tiff':'🖼️',
    '.mp4':'🎬','.avi':'🎬','.mov':'🎬','.mkv':'🎬','.webm':'🎬',
    '.mp3':'🎵','.wav':'🎵','.flac':'🎵','.aac':'🎵','.ogg':'🎵',
    '.zip':'📦','.rar':'📦','.tar':'📦','.gz':'📦','.7z':'📦',
    '.java':'☕','.cpp':'⚙️','.c':'⚙️','.h':'⚙️','.go':'🔵','.rs':'🦀',
    '.php':'🐘','.dart':'🎯','.vue':'💚','.jsx':'⚛️','.tsx':'⚛️',
    '.rb':'💎','.swift':'🍎','.kt':'🟣','.r':'📊','.m':'🟠',
    '.pdf':'📕','.doc':'📘','.docx':'📘','.xls':'📗','.xlsx':'📗',
    '.ppt':'📙','.pptx':'📙','.csv':'📊',
    '.toml':'⚙️','.ini':'⚙️','.lock':'🔒','.env':'🔒',
    '.dockerfile':'🐳','.gitignore':'🚫','.htaccess':'🔧',
    '.wasm':'🕸️','.so':'🔧','.dll':'🔧','.exe':'💻',
}

C = {
    "bg":          "#050810",
    "bg2":         "#0a0f1e",
    "sidebar":     "#080d1a",
    "card":        "#0d1528",
    "card2":       "#111c35",
    "input":       "#060b18",
    "border":      "#1a2744",
    "border_hi":   "#2a4080",
    "text":        "#e8f0fe",
    "sub":         "#8ba3cc",
    "muted":       "#4a6080",
    "blue1":       "#1a73e8",
    "blue2":       "#0d47a1",
    "blue3":       "#4fc3f7",
    "blue4":       "#00b4ff",
    "blue5":       "#0066ff",
    "cyan":        "#00e5ff",
    "purple":      "#7c4dff",
    "green":       "#00c853",
    "green2":      "#69f0ae",
    "orange":      "#ff9100",
    "red":         "#ff1744",
    "grad1":       "#0d47a1",
    "grad2":       "#1565c0",
    "grad3":       "#1976d2",
    "grad4":       "#42a5f5",
    "accent":      "#00b4ff",
    "yellow":      "#ffd600",
}

def icon_for(ext):
    return FILE_ICONS.get(ext.lower(), "📄")

def fmt_size(b):
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    if b < 1024**3: return f"{b/1024**2:.1f} MB"
    return f"{b/1024**3:.1f} GB"

def fmt_time(s):
    if s < 60: return f"{s:.1f}s"
    if s < 3600: return f"{s/60:.1f}m"
    return f"{s/3600:.1f}h"

def get_file_type(ext):
    images = {'.png','.jpg','.jpeg','.gif','.svg','.webp','.ico','.bmp','.tiff'}
    videos = {'.mp4','.avi','.mov','.mkv','.webm'}
    audio  = {'.mp3','.wav','.flac','.aac','.ogg'}
    zips   = {'.zip','.rar','.tar','.gz','.7z'}
    code   = {'.py','.js','.ts','.java','.cpp','.c','.go','.rs','.php',
              '.html','.css','.jsx','.tsx','.vue','.rb','.swift','.kt'}
    docs   = {'.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx'}
    if ext in images: return "image"
    if ext in videos: return "video"
    if ext in audio:  return "audio"
    if ext in zips:   return "archive"
    if ext in code:   return "code"
    if ext in docs:   return "document"
    return "other"


# ══════════════════════════════════════════════════════════════
#  TOOLTIP
# ══════════════════════════════════════════════════════════════
class Tip:
    def __init__(self, w, text):
        self.w = w; self.text = text; self.tip = None
        w.bind("<Enter>", self.show); w.bind("<Leave>", self.hide)
    def show(self, e=None):
        if self.tip: return
        x = self.w.winfo_rootx() + 20
        y = self.w.winfo_rooty() + self.w.winfo_height() + 4
        self.tip = tw = tk.Toplevel(self.w)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        f = tk.Frame(tw, bg=C["border_hi"], bd=1)
        f.pack()
        tk.Label(f, text=self.text, bg=C["card2"], fg=C["text"],
                font=("Segoe UI", 9), padx=10, pady=5).pack()
    def hide(self, e=None):
        if self.tip: self.tip.destroy(); self.tip = None


# ══════════════════════════════════════════════════════════════
#  GRADIENT CANVAS
# ══════════════════════════════════════════════════════════════
class GradientFrame(tk.Canvas):
    def __init__(self, parent, c1, c2, height=4, **kw):
        super().__init__(parent, height=height, highlightthickness=0, **kw)
        self.c1 = c1; self.c2 = c2
        self.bind("<Configure>", self._draw)
    def _draw(self, e=None):
        self.delete("all")
        w = self.winfo_width(); h = self.winfo_height()
        if w < 2: return
        r1,g1,b1 = self.winfo_rgb(self.c1)
        r2,g2,b2 = self.winfo_rgb(self.c2)
        for i in range(w):
            r = int(r1 + (r2-r1)*i/w) >> 8
            g = int(g1 + (g2-g1)*i/w) >> 8
            b = int(b1 + (b2-b1)*i/w) >> 8
            self.create_line(i,0,i,h, fill=f"#{r:02x}{g:02x}{b:02x}")


# ══════════════════════════════════════════════════════════════
#  GITHUB ENGINE  ← + move_file & rename_file
# ══════════════════════════════════════════════════════════════
class GitHubEngine:
    def __init__(self, token):
        self.token = token
        self.gh    = Github(token, per_page=100)
        self.user  = self.gh.get_user()

    @property
    def username(self): return self.user.login

    # ── Repos ──
    def list_repos(self):
        out = []
        for r in self.user.get_repos(affiliation="owner", sort="updated"):
            out.append({"full_name":r.full_name,"name":r.name,
                        "private":r.private,"description":r.description or "",
                        "default_branch":r.default_branch,"url":r.html_url,
                        "stars":r.stargazers_count,"lang":r.language or ""})
        return out

    def create_repo(self, name, desc="", private=False):
        return self.user.create_repo(name=name,description=desc,
                                     private=private,auto_init=True)

    # ── Branches ──
    def list_branches(self, full_name):
        return [b.name for b in self.gh.get_repo(full_name).get_branches()]

    def create_branch(self, full_name, new_br, src="main"):
        repo = self.gh.get_repo(full_name)
        sha  = repo.get_branch(src).commit.sha
        repo.create_git_ref(ref=f"refs/heads/{new_br}", sha=sha)

    # ── Remote Files ──
    def list_remote_files(self, full_name, branch):
        repo  = self.gh.get_repo(full_name)
        files = []
        self._recurse(repo, "", branch, files)
        return files

    def _recurse(self, repo, path, branch, result):
        try:
            items = repo.get_contents(path, ref=branch)
            if not isinstance(items, list): items = [items]
            for c in items:
                if c.type == "dir":
                    self._recurse(repo, c.path, branch, result)
                else:
                    result.append({"path":c.path,"sha":c.sha,
                                   "size":c.size,"url":c.download_url})
        except: pass

    def get_file(self, full_name, path, branch):
        repo = self.gh.get_repo(full_name)
        c    = repo.get_contents(path, ref=branch)
        return c.decoded_content, c.sha   # return bytes + sha

    def update_file(self, full_name, path, content, sha, branch, msg):
        repo = self.gh.get_repo(full_name)
        if isinstance(content, str): content = content.encode()
        repo.update_file(path=path, message=msg, content=content,
                        sha=sha, branch=branch)

    def create_file_raw(self, full_name, path, content, branch, msg):
        """Create file (bytes or str)"""
        repo = self.gh.get_repo(full_name)
        if isinstance(content, str): content = content.encode()
        repo.create_file(path=path, message=msg,
                        content=content, branch=branch)

    def delete_file(self, full_name, path, sha, branch, msg):
        self.gh.get_repo(full_name).delete_file(
            path=path, message=msg, sha=sha, branch=branch)

    def create_folder(self, full_name, folder_path, branch, msg):
        repo      = self.gh.get_repo(full_name)
        keep_path = folder_path.rstrip("/") + "/.gitkeep"
        repo.create_file(path=keep_path, message=msg,
                        content=b"", branch=branch)

    # ══════════════════════════════════════════════════
    #  ★ MOVE / RENAME FILE ★
    # ══════════════════════════════════════════════════
    def move_file(self, full_name, src_path, dst_path,
                  branch, commit_msg=None):
        """
        Move (or rename) a file in the GitHub repository.
        Steps:
          1. Read source content + sha
          2. Create file at destination path
          3. Delete source file
        """
        repo = self.gh.get_repo(full_name)

        # 1. Read source
        src_content_obj = repo.get_contents(src_path, ref=branch)
        raw_content     = src_content_obj.decoded_content
        src_sha         = src_content_obj.sha

        if not commit_msg:
            commit_msg = f"Move {src_path} → {dst_path}"

        # 2. Create at destination
        # Check if destination already exists
        dst_exists = False
        dst_sha    = None
        try:
            dst_obj    = repo.get_contents(dst_path, ref=branch)
            dst_exists = True
            dst_sha    = dst_obj.sha
        except Exception:
            pass

        if dst_exists:
            repo.update_file(path=dst_path,
                            message=f"{commit_msg} (overwrite)",
                            content=raw_content,
                            sha=dst_sha,
                            branch=branch)
        else:
            repo.create_file(path=dst_path,
                            message=f"{commit_msg} (create at dest)",
                            content=raw_content,
                            branch=branch)

        # 3. Delete source
        repo.delete_file(path=src_path,
                        message=f"{commit_msg} (remove source)",
                        sha=src_sha,
                        branch=branch)

        return dst_path

    def rename_file(self, full_name, old_path, new_name,
                    branch, commit_msg=None):
        """
        Rename a file (keep same folder, change filename only).
        """
        folder   = os.path.dirname(old_path)
        dst_path = (folder + "/" + new_name).lstrip("/")
        return self.move_file(full_name, old_path, dst_path,
                              branch, commit_msg or f"Rename {old_path} → {dst_path}")

    # ── Get SHA map ──
    def get_sha_map(self, full_name, branch):
        return {f["path"]: f["sha"]
                for f in self.list_remote_files(full_name, branch)}

    # ── Scan local items ──
    def scan_items(self, items):
        result   = []
        tmp_dirs = []
        for item_path in items:
            item_path = item_path.strip().strip("{}\"'")
            if not os.path.exists(item_path): continue
            if os.path.isdir(item_path):
                self._scan_dir(item_path,
                               os.path.basename(item_path), result)
            elif item_path.lower().endswith(".zip"):
                tmp = tempfile.mkdtemp()
                tmp_dirs.append(tmp)
                try:
                    with zipfile.ZipFile(item_path,'r') as zf:
                        zf.extractall(tmp)
                    zip_name = os.path.splitext(
                        os.path.basename(item_path))[0]
                    self._scan_dir(tmp, zip_name, result)
                except: pass
            elif os.path.isfile(item_path):
                fname = os.path.basename(item_path)
                result.append({
                    "full_path": item_path,
                    "rel_path":  fname,
                    "size":      os.path.getsize(item_path),
                    "ext":       os.path.splitext(fname)[1].lower() or ".file"
                })
        for r in result:
            r["_tmp"] = tmp_dirs
        return result

    def _scan_dir(self, base_path, prefix, result):
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if fname in SKIP_DIRS: continue
                fp  = os.path.join(root, fname)
                rel = os.path.relpath(fp,
                      os.path.dirname(base_path)).replace("\\","/")
                result.append({
                    "full_path": fp,
                    "rel_path":  rel,
                    "size":      os.path.getsize(fp),
                    "ext":       os.path.splitext(fname)[1].lower() or ".file"
                })

    def upload_items(self, full_name, items, branch="main",
                     commit_msg="Upload", target_folder="",
                     callback=None):
        repo        = self.gh.get_repo(full_name)
        sha_map     = self.get_sha_map(full_name, branch)
        total       = len(items)
        uploaded    = 0; total_bytes = 0; errors = []
        t0          = time.time()

        if callback: callback("start", {"total": total})

        for i, f in enumerate(items):
            rel = f["rel_path"]
            if target_folder:
                rel = target_folder.strip("/") + "/" + rel

            try:
                with open(f["full_path"],"rb") as fh:
                    content = fh.read()

                if callback:
                    callback("uploading",{"file":rel,"index":i+1,
                                          "total":total,"size":f["size"]})

                if rel in sha_map:
                    repo.update_file(path=rel,
                        message=f"{commit_msg} - update {rel}",
                        content=content, sha=sha_map[rel], branch=branch)
                else:
                    repo.create_file(path=rel,
                        message=f"{commit_msg} - add {rel}",
                        content=content, branch=branch)

                uploaded    += 1
                total_bytes += f["size"]
                elapsed      = time.time() - t0
                speed        = total_bytes/elapsed if elapsed>0 else 0

                if callback:
                    callback("progress",{"file":rel,"uploaded":uploaded,
                                         "total":total,"bytes":total_bytes,
                                         "speed":speed})
            except Exception as e:
                errors.append({"file":rel,"error":str(e)})
                if callback:
                    callback("file_error",{"file":rel,"error":str(e)})

        elapsed = time.time()-t0
        if callback:
            callback("done",{"uploaded":uploaded,"total":total,
                             "bytes":total_bytes,"errors":errors,
                             "elapsed":elapsed})
        return uploaded, total, errors


# ══════════════════════════════════════════════════════════════
#  MOVE FILE DIALOG
# ══════════════════════════════════════════════════════════════
class MoveFileDialog(tk.Toplevel):
    """
    Beautiful dialog to move or rename a remote file.
    Shows folder tree built from remote file list.
    Result stored in self.result = new_path  (or None if cancelled)
    """

    def __init__(self, parent, src_path, remote_files, colors):
        super().__init__(parent)
        self.result   = None
        self.src_path = src_path
        self.C        = colors

        self.title(f"✂️  Move / Rename File")
        self.geometry("700x560")
        self.configure(bg=self.C["bg"])
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        GradientFrame(self, self.C["blue5"], self.C["cyan"],
                      height=3, bg=self.C["bg"]).pack(fill="x")

        # Header
        hdr = tk.Frame(self, bg=self.C["card"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✂️  Move / Rename File",
                font=("Segoe UI",12,"bold"),
                bg=self.C["card"], fg=self.C["text"]).pack(side="left")
        tk.Label(hdr, text="Select destination folder or type path",
                font=("Segoe UI",9),
                bg=self.C["card"], fg=self.C["sub"]).pack(side="right")

        # Source info
        src_f = tk.Frame(self, bg=self.C["card2"], padx=16, pady=8)
        src_f.pack(fill="x", padx=8, pady=(6,0))
        tk.Label(src_f, text="📄  Source:",
                font=("Segoe UI",9,"bold"),
                bg=self.C["card2"], fg=self.C["sub"]).pack(side="left")
        tk.Label(src_f, text=src_path,
                font=("Consolas",10),
                bg=self.C["card2"], fg=self.C["blue3"]).pack(side="left", padx=8)

        # Build folder tree
        folders = self._extract_folders(remote_files)

        # Two-pane: folder tree | destination preview
        body = tk.Frame(self, bg=self.C["bg"])
        body.pack(fill="both", expand=True, padx=8, pady=8)

        # LEFT — Folder tree
        left = tk.Frame(body, bg=self.C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0,4))

        tk.Label(left, text="📁  Repository Folders",
                font=("Segoe UI",9,"bold"),
                bg=self.C["bg"], fg=self.C["blue3"]).pack(anchor="w", pady=(0,4))

        tree_f = tk.Frame(left, bg=self.C["bg"])
        tree_f.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Move.Treeview",
                        background=self.C["input"],
                        foreground=self.C["text"],
                        fieldbackground=self.C["input"],
                        borderwidth=0,
                        font=("Segoe UI",10),
                        rowheight=26)
        style.map("Move.Treeview",
                  background=[("selected", self.C["blue2"])])
        style.configure("Move.Treeview.Heading",
                        background=self.C["card2"],
                        foreground=self.C["blue3"],
                        font=("Segoe UI",9,"bold"))

        self.folder_tree = ttk.Treeview(tree_f,
                                        columns=("name",),
                                        show="tree headings",
                                        style="Move.Treeview")
        self.folder_tree.heading("name", text="Folder Path")
        self.folder_tree.column("#0", width=30)
        self.folder_tree.column("name", width=260)

        fts = ttk.Scrollbar(tree_f, orient="vertical",
                            command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=fts.set)
        fts.pack(side="right", fill="y")
        self.folder_tree.pack(fill="both", expand=True)

        # Root entry
        root_id = self.folder_tree.insert("","end",
                                          values=("  /  (root)",),
                                          text="📁", open=True)
        self.folder_tree.tag_configure("folder",
                                       foreground=self.C["blue3"])
        self.folder_tree.item(root_id, tags=("folder",))
        self._root_id = root_id

        # Insert folders
        folder_ids = {"": root_id}
        for folder in sorted(folders):
            parts  = folder.split("/")
            parent = ""
            for i, part in enumerate(parts):
                cur_path = "/".join(parts[:i+1])
                if cur_path not in folder_ids:
                    par_id = folder_ids.get(parent, root_id)
                    fid    = self.folder_tree.insert(
                        par_id,"end",
                        values=(f"  📁  {cur_path}",),
                        text="📁", open=False)
                    self.folder_tree.item(fid, tags=("folder",))
                    folder_ids[cur_path] = fid
                parent = cur_path

        self.folder_tree.bind("<<TreeviewSelect>>", self._on_folder_sel)

        # RIGHT — Destination settings
        right = tk.Frame(body, bg=self.C["bg"], width=260)
        right.pack(side="right", fill="y", padx=(4,0))
        right.pack_propagate(False)

        tk.Label(right, text="🎯  Destination",
                font=("Segoe UI",9,"bold"),
                bg=self.C["bg"], fg=self.C["blue3"]).pack(anchor="w", pady=(0,4))

        # Selected folder display
        sf_wrap = tk.Frame(right, bg=self.C["border"])
        sf_wrap.pack(fill="x", pady=(0,8))
        sf_in = tk.Frame(sf_wrap, bg=self.C["input"])
        sf_in.pack(fill="x", padx=1, pady=1)
        tk.Label(sf_in, text="📁", bg=self.C["input"],
                font=("Segoe UI",10)).pack(side="left", padx=6)
        self.lbl_folder = tk.Label(sf_in, text="/  (root)",
                                   font=("Consolas",9),
                                   bg=self.C["input"], fg=self.C["cyan"])
        self.lbl_folder.pack(side="left", fill="x", expand=True, pady=6)

        # Or type folder manually
        tk.Label(right, text="Or type destination folder:",
                font=("Segoe UI",9),
                bg=self.C["bg"], fg=self.C["sub"]).pack(anchor="w", pady=(0,4))
        tf_w = tk.Frame(right, bg=self.C["border"])
        tf_w.pack(fill="x", pady=(0,8))
        tf_i = tk.Frame(tf_w, bg=self.C["input"])
        tf_i.pack(fill="x", padx=1, pady=1)
        tk.Label(tf_i, text="📁", bg=self.C["input"],
                font=("Segoe UI",9)).pack(side="left", padx=4)
        self.ent_folder = tk.Entry(tf_i, font=("Consolas",10),
                                   bg=self.C["input"], fg=self.C["cyan"],
                                   insertbackground=self.C["cyan"],
                                   relief="flat", bd=5)
        self.ent_folder.pack(fill="x", expand=True)
        self.ent_folder.bind("<KeyRelease>", self._on_folder_type)

        GradientFrame(right, self.C["blue5"], self.C["purple"],
                      height=1, bg=self.C["bg"]).pack(fill="x", pady=8)

        # New filename
        tk.Label(right, text="✏️  New Filename (rename):",
                font=("Segoe UI",9),
                bg=self.C["bg"], fg=self.C["sub"]).pack(anchor="w", pady=(0,4))
        fn_w = tk.Frame(right, bg=self.C["border"])
        fn_w.pack(fill="x", pady=(0,8))
        fn_i = tk.Frame(fn_w, bg=self.C["input"])
        fn_i.pack(fill="x", padx=1, pady=1)
        tk.Label(fn_i, text="✏️", bg=self.C["input"],
                font=("Segoe UI",9)).pack(side="left", padx=4)
        self.ent_filename = tk.Entry(fn_i, font=("Consolas",10),
                                     bg=self.C["input"], fg=self.C["text"],
                                     insertbackground=self.C["text"],
                                     relief="flat", bd=5)
        self.ent_filename.pack(fill="x", expand=True)
        # Default = original filename
        self.ent_filename.insert(0, os.path.basename(src_path))
        self.ent_filename.bind("<KeyRelease>", self._update_preview)

        GradientFrame(right, self.C["purple"], self.C["cyan"],
                      height=1, bg=self.C["bg"]).pack(fill="x", pady=8)

        # Preview
        tk.Label(right, text="👁  Result Preview:",
                font=("Segoe UI",9),
                bg=self.C["bg"], fg=self.C["sub"]).pack(anchor="w", pady=(0,4))

        prev_wrap = tk.Frame(right, bg=self.C["border"])
        prev_wrap.pack(fill="x", pady=(0,8))
        prev_in = tk.Frame(prev_wrap, bg=self.C["card"])
        prev_in.pack(fill="x", padx=1, pady=1)
        self.lbl_preview = tk.Label(prev_in,
                                    text=src_path,
                                    font=("Consolas",9),
                                    bg=self.C["card"],
                                    fg=self.C["green"],
                                    wraplength=240,
                                    justify="left",
                                    padx=8, pady=8)
        self.lbl_preview.pack(fill="x")

        self._selected_folder = ""
        self._update_preview()

        # Commit message
        tk.Label(right, text="💬  Commit Message:",
                font=("Segoe UI",9),
                bg=self.C["bg"], fg=self.C["sub"]).pack(anchor="w", pady=(0,4))
        cm_w = tk.Frame(right, bg=self.C["border"])
        cm_w.pack(fill="x", pady=(0,8))
        cm_i = tk.Frame(cm_w, bg=self.C["input"])
        cm_i.pack(fill="x", padx=1, pady=1)
        self.ent_commit = tk.Entry(cm_i, font=("Segoe UI",9),
                                   bg=self.C["input"], fg=self.C["text"],
                                   insertbackground=self.C["text"],
                                   relief="flat", bd=5)
        self.ent_commit.pack(fill="x", expand=True)
        self.ent_commit.insert(0, f"Move {os.path.basename(src_path)}")

        # Bottom buttons
        GradientFrame(self, self.C["blue5"], self.C["cyan"],
                      height=1, bg=self.C["bg"]).pack(fill="x", padx=0, pady=(0,0))

        bot = tk.Frame(self, bg=self.C["card"], padx=16, pady=10)
        bot.pack(fill="x")

        tk.Button(bot, text="✖ Cancel",
                 bg=self.C["border"], fg=self.C["text"],
                 font=("Segoe UI",10,"bold"), relief="flat",
                 padx=16, pady=7, cursor="hand2",
                 command=self.destroy).pack(side="right", padx=(8,0))

        tk.Button(bot, text="✅  Move File",
                 bg=self.C["blue1"], fg="#fff",
                 font=("Segoe UI",10,"bold"), relief="flat",
                 padx=20, pady=7, cursor="hand2",
                 command=self._confirm).pack(side="right")

        tk.Label(bot,
                text="💡 Move = read → create at dest → delete source (2 commits)",
                font=("Segoe UI",8),
                bg=self.C["card"], fg=self.C["muted"]).pack(side="left")

        self.wait_window()

    def _extract_folders(self, remote_files):
        folders = set()
        for f in remote_files:
            parts = f["path"].split("/")
            for i in range(len(parts)-1):
                folders.add("/".join(parts[:i+1]))
        return sorted(folders)

    def _on_folder_sel(self, e=None):
        sel = self.folder_tree.selection()
        if not sel: return
        vals = self.folder_tree.item(sel[0], "values")
        if not vals: return
        raw = vals[0].strip()
        # Remove icon prefix
        for pfx in ["📁  ","  /  (root)"]:
            if raw == "  /  (root)":
                raw = ""
                break
            if raw.startswith("📁  "):
                raw = raw[4:].strip()
                break
        self._selected_folder = raw
        self.ent_folder.delete(0,"end")
        self.ent_folder.insert(0, raw)
        self.lbl_folder.config(text=f"/{raw}" if raw else "/  (root)")
        self._update_preview()

    def _on_folder_type(self, e=None):
        self._selected_folder = self.ent_folder.get().strip().strip("/")
        self._update_preview()

    def _update_preview(self, e=None):
        folder   = self._selected_folder
        filename = self.ent_filename.get().strip() or os.path.basename(self.src_path)
        if folder:
            new_path = folder.strip("/") + "/" + filename
        else:
            new_path = filename
        self.lbl_preview.config(text=new_path)
        self._new_path = new_path

    def _confirm(self):
        self._update_preview()
        new_path = getattr(self, "_new_path", None)
        if not new_path:
            messagebox.showwarning("⚠️","No destination set!", parent=self)
            return
        if new_path == self.src_path:
            messagebox.showwarning("⚠️",
                "Source and destination are the same!\n"
                "Please change the folder or filename.", parent=self)
            return
        self.result = {
            "new_path":   new_path,
            "commit_msg": self.ent_commit.get().strip()
                          or f"Move {self.src_path} → {new_path}"
        }
        self.destroy()


# ══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════
class App:

    def __init__(self):
        self.engine        = None
        self.repos         = []
        self.remote_files  = []
        self.scanned_files = []
        self.is_uploading  = False
        self.config        = self._load_cfg()

        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("GitHub Uploader Pro  ·  v4.1")
        self.root.geometry("1200x750")
        self.root.minsize(1000,650)
        self.root.configure(bg=C["bg"])

        self._styles()
        self._build()
        self._load_token()
        self.root.mainloop()

    # ── Config ──
    def _load_cfg(self):
        try:
            with open(CONFIG_FILE) as f: return json.load(f)
        except: return {}

    def _save_cfg(self):
        try:
            with open(CONFIG_FILE,"w") as f: json.dump(self.config, f)
        except: pass

    def _load_token(self):
        t = self.config.get("token","")
        if t: self.ent_token.insert(0, t)

    # ── Styles ──
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        for w in ("TCombobox","TEntry"):
            s.configure(w, fieldbackground=C["input"],
                        background=C["border"], foreground=C["text"],
                        insertcolor=C["text"], arrowcolor=C["blue3"],
                        selectbackground=C["blue2"],
                        selectforeground=C["text"],
                        darkcolor=C["input"], lightcolor=C["input"],
                        bordercolor=C["border"], relief="flat")
            s.map(w, fieldbackground=[("readonly",C["input"])],
                  foreground=[("readonly",C["text"])])
        s.configure("Treeview",
                    background=C["input"], foreground=C["text"],
                    fieldbackground=C["input"], borderwidth=0,
                    font=("Consolas",9), rowheight=22)
        s.map("Treeview", background=[("selected",C["blue2"])])
        s.configure("Treeview.Heading",
                    background=C["card2"], foreground=C["blue3"],
                    font=("Segoe UI",9,"bold"), relief="flat")
        for sb in ("Vertical.TScrollbar","Horizontal.TScrollbar"):
            s.configure(sb, background=C["border"],
                        troughcolor=C["bg2"], arrowcolor=C["sub"])

    # ── Widget helpers ──
    def _btn(self, parent, text, bg, cmd, **kw):
        return tk.Button(parent, text=text, bg=bg, fg="#fff",
                        font=("Segoe UI",9,"bold"), relief="flat",
                        cursor="hand2", activebackground=bg,
                        activeforeground="#fff", command=cmd, **kw)

    def _stat(self, parent, label, val, color):
        f = tk.Frame(parent, bg=C["input"], padx=12, pady=8)
        f.pack(side="left", fill="x", expand=True, padx=3)
        v = tk.Label(f, text=val, font=("Segoe UI",14,"bold"),
                    bg=C["input"], fg=color)
        v.pack()
        tk.Label(f, text=label, font=("Segoe UI",8),
                bg=C["input"], fg=C["muted"]).pack()
        return v

    def _log(self, msg, tag="m"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] ","m")
        self.log_box.insert("end", f"{msg}\n", tag)
        self.log_box.see("end")

    def _toggle_pw(self, e=None):
        self._show_pw = not getattr(self,"_show_pw",False)
        self.ent_token.config(show="" if self._show_pw else "•")

    def _validate_upload(self):
        ok = (self.engine is not None
              and len(self.scanned_files) > 0
              and bool(self.repo_var.get())
              and not self.is_uploading)
        if ok:
            self.btn_upload.config(state="normal",bg=C["blue1"],cursor="hand2")
        else:
            self.btn_upload.config(state="disabled",bg=C["border"],cursor="arrow")

    def _get_repo(self):
        d = self.repo_var.get()
        if not d: return None
        for pfx in ["🔒 ","🌐 "]:
            if d.startswith(pfx): d = d[len(pfx):]
        return d.strip().split()[-1] if d.strip() else None

    def _get_branch(self):
        return self.branch_combo.get().strip() or "main"

    # ══════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════
    def _build(self):
        GradientFrame(self.root, C["blue5"], C["cyan"],
                      height=3, bg=C["bg"]).pack(fill="x")
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(main, bg=C["sidebar"], width=280)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        tk.Frame(main, bg=C["border"], width=1).pack(side="left", fill="y")

        # Right
        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_sidebar(self):
        sb = self._sidebar

        # Logo
        logo_f = tk.Frame(sb, bg=C["sidebar"])
        logo_f.pack(fill="x", pady=(16,8))
        lc = tk.Canvas(logo_f, width=44, height=44,
                      bg=C["sidebar"], highlightthickness=0)
        lc.pack(side="left", padx=(14,8))
        lc.create_oval(2,2,42,42, fill=C["blue2"],
                      outline=C["blue3"], width=2)
        lc.create_text(22,22, text="⬆", fill=C["cyan"],
                      font=("Segoe UI",18,"bold"))
        tf = tk.Frame(logo_f, bg=C["sidebar"])
        tf.pack(side="left")
        tk.Label(tf, text="GitHub", font=("Segoe UI",13,"bold"),
                bg=C["sidebar"], fg=C["text"]).pack(anchor="w")
        tk.Label(tf, text="Uploader Pro", font=("Segoe UI",8),
                bg=C["sidebar"], fg=C["sub"]).pack(anchor="w")
        tk.Label(sb, text=" v4.1 ULTRA", bg=C["purple"], fg="#fff",
                font=("Segoe UI",7,"bold"), padx=6, pady=2).pack(pady=(0,4))

        GradientFrame(sb, C["blue5"], C["cyan"],
                      height=2, bg=C["sidebar"]).pack(fill="x", pady=(0,12))

        # Auth
        self._sb_section(sb, "🔑  AUTHENTICATION")
        tok_wrap = tk.Frame(sb, bg=C["border"])
        tok_wrap.pack(fill="x", padx=12, pady=(4,0))
        tok_in = tk.Frame(tok_wrap, bg=C["input"])
        tok_in.pack(fill="x", padx=1, pady=1)
        tk.Label(tok_in, text="🔑", bg=C["input"],
                font=("Segoe UI",10)).pack(side="left", padx=(6,3))
        self.ent_token = tk.Entry(tok_in, show="•", font=("Consolas",10),
                                  bg=C["input"], fg=C["text"],
                                  insertbackground=C["text"], relief="flat", bd=5)
        self.ent_token.pack(side="left", fill="x", expand=True)
        eye = tk.Label(tok_in, text="👁", bg=C["input"],
                      font=("Segoe UI",10), cursor="hand2")
        eye.pack(side="right", padx=6)
        eye.bind("<Button-1>", self._toggle_pw)

        self.btn_conn = self._btn(sb, "⚡  Connect to GitHub",
                                 C["blue1"], self.do_connect,
                                 padx=12, pady=8)
        self.btn_conn.pack(fill="x", padx=12, pady=(8,4))

        self.lbl_status = tk.Label(sb, text="⚪ Not connected",
                                   font=("Segoe UI",9),
                                   bg=C["sidebar"], fg=C["muted"])
        self.lbl_status.pack(pady=(0,4))

        link = tk.Label(sb, text="Create token →",
                       font=("Segoe UI",8,"underline"),
                       bg=C["sidebar"], fg=C["blue3"], cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e: webbrowser.open(
            "https://github.com/settings/tokens/new?scopes=repo,delete_repo"))

        GradientFrame(sb, C["blue5"], C["purple"],
                      height=1, bg=C["sidebar"]).pack(fill="x", padx=12, pady=10)

        # Repo
        self._sb_section(sb, "📦  REPOSITORY")
        self.repo_var   = tk.StringVar()
        self.repo_combo = ttk.Combobox(sb, textvariable=self.repo_var,
                                       state="readonly", font=("Segoe UI",9))
        self.repo_combo.pack(fill="x", padx=12, pady=(4,2))
        self.repo_combo.bind("<<ComboboxSelected>>", self._on_repo_sel)

        rbr = tk.Frame(sb, bg=C["sidebar"])
        rbr.pack(fill="x", padx=12, pady=(4,4))
        self._btn(rbr, "🔄", C["border"], self.do_refresh_repos,
                 padx=8, pady=5).pack(side="left", padx=(0,4))
        self._btn(rbr, "➕ New Repo", C["blue2"],
                 self.do_create_repo, padx=8, pady=5).pack(side="left")

        self.lbl_repo_info = tk.Label(sb, text="",
                                     font=("Segoe UI",8),
                                     bg=C["sidebar"], fg=C["sub"],
                                     wraplength=240, justify="left")
        self.lbl_repo_info.pack(anchor="w", padx=12, pady=(0,4))

        nr_w = tk.Frame(sb, bg=C["border"])
        nr_w.pack(fill="x", padx=12, pady=(2,0))
        nr_i = tk.Frame(nr_w, bg=C["input"])
        nr_i.pack(fill="x", padx=1, pady=1)
        self.ent_newrepo = tk.Entry(nr_i, font=("Segoe UI",9),
                                    bg=C["input"], fg=C["sub"],
                                    insertbackground=C["text"],
                                    relief="flat", bd=5)
        self.ent_newrepo.pack(side="left", fill="x", expand=True)
        self.ent_newrepo.insert(0, "repo-name")
        self.ent_newrepo.bind("<FocusIn>",
            lambda e: self.ent_newrepo.delete(0,"end")
            if self.ent_newrepo.get()=="repo-name" else None)
        self.priv_var = tk.BooleanVar(value=False)
        tk.Checkbutton(nr_i, text="🔒", variable=self.priv_var,
                      bg=C["input"], fg=C["sub"],
                      selectcolor=C["border"],
                      activebackground=C["input"],
                      font=("Segoe UI",9)).pack(side="right", padx=4)

        GradientFrame(sb, C["purple"], C["blue5"],
                      height=1, bg=C["sidebar"]).pack(fill="x", padx=12, pady=10)

        # Branch
        self._sb_section(sb, "🌿  BRANCH & COMMIT")
        br_row = tk.Frame(sb, bg=C["sidebar"])
        br_row.pack(fill="x", padx=12, pady=(4,4))
        self.branch_combo = ttk.Combobox(br_row, font=("Segoe UI",9), width=12)
        self.branch_combo.pack(side="left", fill="x", expand=True, padx=(0,4))
        self.branch_combo.set("main")
        self._btn(br_row, "🌿+", C["border"],
                 self.do_create_branch, padx=6, pady=4).pack(side="right")

        # Target folder
        tf_w = tk.Frame(sb, bg=C["border"])
        tf_w.pack(fill="x", padx=12, pady=(0,4))
        tf_i = tk.Frame(tf_w, bg=C["input"])
        tf_i.pack(fill="x", padx=1, pady=1)
        tk.Label(tf_i, text="📁", bg=C["input"],
                font=("Segoe UI",9)).pack(side="left", padx=(6,2))
        self.ent_target = tk.Entry(tf_i, font=("Segoe UI",9),
                                   bg=C["input"], fg=C["sub"],
                                   insertbackground=C["text"],
                                   relief="flat", bd=4)
        self.ent_target.pack(fill="x", expand=True)
        self.ent_target.insert(0, "target/folder (optional)")
        self.ent_target.bind("<FocusIn>",
            lambda e: self.ent_target.delete(0,"end")
            if "optional" in self.ent_target.get() else None)

        # Commit
        cm_w = tk.Frame(sb, bg=C["border"])
        cm_w.pack(fill="x", padx=12, pady=(0,4))
        cm_i = tk.Frame(cm_w, bg=C["input"])
        cm_i.pack(fill="x", padx=1, pady=1)
        tk.Label(cm_i, text="💬", bg=C["input"],
                font=("Segoe UI",9)).pack(side="left", padx=(6,2))
        self.ent_commit = tk.Entry(cm_i, font=("Segoe UI",9),
                                   bg=C["input"], fg=C["text"],
                                   insertbackground=C["text"],
                                   relief="flat", bd=4)
        self.ent_commit.pack(fill="x", expand=True)
        self.ent_commit.insert(0, "Upload via GitHub Uploader Pro 🚀")

        tk.Frame(sb, bg=C["sidebar"]).pack(fill="y", expand=True)
        GradientFrame(sb, C["cyan"], C["blue5"],
                      height=1, bg=C["sidebar"]).pack(fill="x", padx=12, pady=(0,8))
        tk.Label(sb, text="GitHub Uploader Pro v4.1",
                font=("Segoe UI",7), bg=C["sidebar"],
                fg=C["muted"]).pack(pady=(0,8))

    def _sb_section(self, parent, title):
        f = tk.Frame(parent, bg=C["sidebar"])
        f.pack(fill="x", padx=12, pady=(8,4))
        tk.Label(f, text=title, font=("Segoe UI",9,"bold"),
                bg=C["sidebar"], fg=C["blue3"]).pack(anchor="w")

    def _build_right(self, parent):
        # Top bar
        top = tk.Frame(parent, bg=C["card"], height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="🚀  GitHub Uploader Pro",
                font=("Segoe UI",14,"bold"),
                bg=C["card"], fg=C["text"]).pack(side="left", padx=20, pady=10)

        self.btn_upload = tk.Button(
            top, text="🚀  UPLOAD TO GITHUB",
            font=("Segoe UI",11,"bold"),
            bg=C["border"], fg=C["muted"], relief="flat",
            padx=24, pady=6, cursor="arrow", state="disabled",
            command=self.do_upload)
        self.btn_upload.pack(side="right", padx=16, pady=8)

        self._btn(top, "📁 New Folder", C["card2"],
                 self.do_create_folder, padx=12, pady=6).pack(
                 side="right", padx=(0,8), pady=8)

        GradientFrame(parent, C["blue5"], C["cyan"],
                      height=2, bg=C["bg"]).pack(fill="x")

        # Tabs
        style = ttk.Style()
        style.configure("T.TNotebook", background=C["bg"], borderwidth=0)
        style.configure("T.TNotebook.Tab",
                        background=C["card"], foreground=C["sub"],
                        font=("Segoe UI",10), padding=[16,8])
        style.map("T.TNotebook.Tab",
                  background=[("selected",C["blue2"]),("active",C["card2"])],
                  foreground=[("selected",C["text"]),("active",C["blue3"])])

        self.nb = ttk.Notebook(parent, style="T.TNotebook")
        self.nb.pack(fill="both", expand=True)

        t1 = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(t1, text="  📂  Drop Zone  ")
        self._build_drop_tab(t1)

        t2 = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(t2, text="  🗂️  Remote Files  ")
        self._build_browser_tab(t2)

        t3 = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(t3, text="  📊  Progress & Log  ")
        self._build_progress_tab(t3)

    # ── Tab 1: Drop Zone ──
    def _build_drop_tab(self, parent):
        pane = tk.PanedWindow(parent, orient="horizontal",
                             bg=C["bg"], sashwidth=4)
        pane.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(pane, bg=C["bg"])
        pane.add(left, width=420, minsize=320)

        self.drop_outer = tk.Frame(left, bg=C["border_hi"], bd=2)
        self.drop_outer.pack(fill="both", expand=True, pady=(0,8))
        self.drop_zone  = tk.Frame(self.drop_outer, bg=C["card"], cursor="hand2")
        self.drop_zone.pack(fill="both", expand=True, padx=2, pady=2)

        dz = tk.Frame(self.drop_zone, bg=C["card"])
        dz.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_dz_icon = tk.Label(dz, text="📥",
                                   font=("Segoe UI",56),
                                   bg=C["card"], fg=C["blue3"])
        self.lbl_dz_icon.pack()
        self.lbl_dz_title = tk.Label(dz, text="Drop Anything Here",
                                    font=("Segoe UI",16,"bold"),
                                    bg=C["card"], fg=C["text"])
        self.lbl_dz_title.pack(pady=(10,4))
        self.lbl_dz_sub = tk.Label(dz,
            text="Files • Folders • ZIP • Images • Videos • Audio • Code • Docs",
            font=("Segoe UI",10), bg=C["card"],
            fg=C["sub"], justify="center")
        self.lbl_dz_sub.pack()

        GradientFrame(dz, C["blue5"], C["cyan"],
                      height=2, bg=C["card"]).pack(fill="x", pady=10)

        br = tk.Frame(dz, bg=C["card"])
        br.pack()
        self._btn(br,"📁 Folder",C["blue2"],self.browse_folder,
                 padx=14,pady=7).pack(side="left",padx=4)
        self._btn(br,"📄 Files",C["blue1"],self.browse_files,
                 padx=14,pady=7).pack(side="left",padx=4)
        self._btn(br,"📦 ZIP",C["purple"],self.browse_zip,
                 padx=14,pady=7).pack(side="left",padx=4)

        if not DND_AVAILABLE:
            tk.Label(dz,
                    text="💡 pip install tkinterdnd2  for drag & drop",
                    font=("Segoe UI",8),
                    bg=C["card"], fg=C["orange"]).pack(pady=(8,0))

        if DND_AVAILABLE:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind('<<DropEnter>>', self._dnd_enter)
            self.drop_zone.dnd_bind('<<DropLeave>>', self._dnd_leave)
            self.drop_zone.dnd_bind('<<Drop>>', self._dnd_drop)

        for w in [self.drop_zone, dz, self.lbl_dz_icon,
                  self.lbl_dz_title, self.lbl_dz_sub]:
            w.bind("<Button-1>", lambda e: self.browse_folder())

        # Stats
        sf = tk.Frame(left, bg=C["card2"])
        sf.pack(fill="x")
        self.stat_files = self._stat(sf,"Files","0",C["blue3"])
        self.stat_size  = self._stat(sf,"Size","—",C["cyan"])
        self.stat_types = self._stat(sf,"Types","—",C["purple"])

        # Queue list
        right = tk.Frame(pane, bg=C["bg"])
        pane.add(right, minsize=280)

        rh = tk.Frame(right, bg=C["card2"])
        rh.pack(fill="x", pady=(0,4))
        tk.Label(rh, text="📋  Upload Queue",
                font=("Segoe UI",10,"bold"),
                bg=C["card2"], fg=C["blue3"]).pack(side="left", padx=12, pady=8)
        self._btn(rh,"🗑 Clear",C["border"],
                 self.clear_queue,padx=8,pady=4).pack(side="right",padx=8,pady=6)

        tf = tk.Frame(right, bg=C["bg"])
        tf.pack(fill="both", expand=True)

        self.queue_tree = ttk.Treeview(tf,
                                       columns=("icon","path","size","type"),
                                       show="headings", height=20,
                                       selectmode="extended")
        self.queue_tree.heading("icon", text="")
        self.queue_tree.heading("path", text="Path")
        self.queue_tree.heading("size", text="Size")
        self.queue_tree.heading("type", text="Type")
        self.queue_tree.column("icon", width=30, anchor="center")
        self.queue_tree.column("path", width=300)
        self.queue_tree.column("size", width=80,  anchor="e")
        self.queue_tree.column("type", width=80,  anchor="center")

        qs = ttk.Scrollbar(tf, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=qs.set)
        qs.pack(side="right", fill="y")
        self.queue_tree.pack(fill="both", expand=True)

        for tag,col in [("image","#42a5f5"),("video","#ab47bc"),
                        ("audio","#ef5350"),("archive","#ff7043"),
                        ("code","#66bb6a"),("document","#ffa726"),
                        ("other",C["sub"])]:
            self.queue_tree.tag_configure(tag, foreground=col)

        self.q_menu = tk.Menu(self.root, tearoff=0,
                             bg=C["card"], fg=C["text"],
                             activebackground=C["blue2"])
        self.q_menu.add_command(label="🗑️ Remove Selected",
                               command=self.remove_from_queue)
        self.queue_tree.bind("<Button-3>", self._q_ctx)

    # ── Tab 2: Remote Files ──
    def _build_browser_tab(self, parent):
        # Toolbar
        tb = tk.Frame(parent, bg=C["card2"])
        tb.pack(fill="x", padx=12, pady=(8,4))

        self._btn(tb,"🔄 Load",C["blue2"],
                 self.do_load_remote,padx=10,pady=6).pack(side="left",padx=(0,3))
        self._btn(tb,"📝 Edit",C["blue1"],
                 self.do_edit_file,padx=10,pady=6).pack(side="left",padx=(0,3))

        # ★ MOVE BUTTON ★
        self.btn_move = self._btn(tb,"✂️ Move",C["purple"],
                                  self.do_move_file,padx=10,pady=6)
        self.btn_move.pack(side="left", padx=(0,3))
        Tip(self.btn_move, "Move or rename selected file to a different folder")

        # ★ RENAME BUTTON ★
        self.btn_rename = self._btn(tb,"✏️ Rename",C["grad2"],
                                    self.do_rename_file,padx=10,pady=6)
        self.btn_rename.pack(side="left", padx=(0,3))
        Tip(self.btn_rename, "Quickly rename selected file (keep same folder)")

        self._btn(tb,"🗑️ Delete",C["red"],
                 self.do_delete_file,padx=10,pady=6).pack(side="left",padx=(0,3))
        self._btn(tb,"📄 New File",C["green"],
                 self.do_create_file,padx=10,pady=6).pack(side="left",padx=(0,3))
        self._btn(tb,"📁 New Folder",C["cyan"],
                 self.do_create_folder,padx=10,pady=6).pack(side="left")

        # Search
        sw = tk.Frame(tb, bg=C["border"])
        sw.pack(side="right", padx=(0,4))
        si = tk.Frame(sw, bg=C["input"])
        si.pack(fill="x", padx=1, pady=1)
        tk.Label(si, text="🔍", bg=C["input"],
                font=("Segoe UI",9)).pack(side="left", padx=4)
        self.ent_search = tk.Entry(si, font=("Segoe UI",9),
                                   bg=C["input"], fg=C["text"],
                                   insertbackground=C["text"],
                                   relief="flat", bd=4, width=20)
        self.ent_search.pack()
        self.ent_search.bind("<KeyRelease>", self._filter_remote)

        # File tree
        tf = tk.Frame(parent, bg=C["bg"])
        tf.pack(fill="both", expand=True, padx=12, pady=(0,8))

        self.remote_tree = ttk.Treeview(tf,
                                        columns=("icon","path","size","sha"),
                                        show="headings", height=25,
                                        selectmode="browse")
        self.remote_tree.heading("icon", text="")
        self.remote_tree.heading("path", text="📄  File Path")
        self.remote_tree.heading("size", text="💾 Size")
        self.remote_tree.heading("sha",  text="SHA")
        self.remote_tree.column("icon", width=30, anchor="center")
        self.remote_tree.column("path", width=580)
        self.remote_tree.column("size", width=100, anchor="e")
        self.remote_tree.column("sha",  width=80)

        rs = ttk.Scrollbar(tf, orient="vertical", command=self.remote_tree.yview)
        self.remote_tree.configure(yscrollcommand=rs.set)
        rs.pack(side="right", fill="y")
        self.remote_tree.pack(fill="both", expand=True)

        for tag,col in [("image","#42a5f5"),("video","#ab47bc"),
                        ("audio","#ef5350"),("archive","#ff7043"),
                        ("code","#66bb6a"),("document","#ffa726"),
                        ("other",C["sub"])]:
            self.remote_tree.tag_configure(tag, foreground=col)

        # Right-click context menu with Move & Rename
        self.rm_menu = tk.Menu(self.root, tearoff=0,
                              bg=C["card"], fg=C["text"],
                              activebackground=C["blue2"])
        self.rm_menu.add_command(label="📝 Edit",    command=self.do_edit_file)
        self.rm_menu.add_command(label="✂️ Move",    command=self.do_move_file)
        self.rm_menu.add_command(label="✏️ Rename",  command=self.do_rename_file)
        self.rm_menu.add_separator()
        self.rm_menu.add_command(label="🗑️ Delete",  command=self.do_delete_file)
        self.remote_tree.bind("<Button-3>", self._rm_ctx)
        self.remote_tree.bind("<Double-1>", lambda e: self.do_edit_file())

    # ── Tab 3: Progress + Log ──
    def _build_progress_tab(self, parent):
        stat_bar = tk.Frame(parent, bg=C["card2"])
        stat_bar.pack(fill="x", padx=12, pady=(8,6))

        self.p_uploaded = self._stat(stat_bar,"Uploaded","0",C["green"])
        self.p_total    = self._stat(stat_bar,"Total","0",C["blue3"])
        self.p_size     = self._stat(stat_bar,"Data","—",C["purple"])
        self.p_speed    = self._stat(stat_bar,"Speed","—",C["orange"])
        self.p_elapsed  = self._stat(stat_bar,"Time","—",C["cyan"])

        pb_outer = tk.Frame(parent, bg=C["border"], height=14)
        pb_outer.pack(fill="x", padx=12, pady=(0,4))
        pb_outer.pack_propagate(False)
        self.pb_canvas = tk.Canvas(pb_outer, height=14,
                                  bg=C["input"], highlightthickness=0)
        self.pb_canvas.pack(fill="both", expand=True, padx=1, pady=1)
        self.pb_rect = self.pb_canvas.create_rectangle(
            0,0,0,14, fill=C["blue1"], outline="")
        self.pb_glow = self.pb_canvas.create_rectangle(
            0,0,0,14, fill=C["cyan"], outline="", stipple="gray50")

        self.lbl_pct = tk.Label(parent, text="0%",
                               font=("Segoe UI",12,"bold"),
                               bg=C["bg"], fg=C["text"])
        self.lbl_pct.pack()

        self.lbl_curfile = tk.Label(parent, text="Ready",
                                   font=("Consolas",9),
                                   bg=C["bg"], fg=C["muted"], wraplength=900)
        self.lbl_curfile.pack(pady=(0,8))

        GradientFrame(parent, C["blue5"], C["purple"],
                      height=1, bg=C["bg"]).pack(fill="x", padx=12, pady=(0,8))

        tk.Label(parent, text="📋  Activity Log",
                font=("Segoe UI",9,"bold"),
                bg=C["bg"], fg=C["blue3"]).pack(anchor="w", padx=12)

        log_f = tk.Frame(parent, bg=C["bg"])
        log_f.pack(fill="both", expand=True, padx=12, pady=(4,8))

        self.log_box = tk.Text(log_f, font=("Consolas",9),
                              bg=C["input"], fg=C["text"],
                              insertbackground=C["text"],
                              relief="flat", bd=8, wrap="word",
                              selectbackground=C["blue2"])
        ls = ttk.Scrollbar(log_f, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=ls.set)
        ls.pack(side="right", fill="y")
        self.log_box.pack(fill="both", expand=True)

        for tag,col in [("g",C["green"]),("b",C["blue3"]),
                        ("r",C["red"]),("o",C["orange"]),
                        ("m",C["muted"]),("c",C["cyan"]),
                        ("p",C["purple"]),("y",C["yellow"]),
                        ("H",C["text"])]:
            self.log_box.tag_config(tag, foreground=col)
        self.log_box.tag_config("H", font=("Consolas",9,"bold"))

        self._log("🚀 GitHub Uploader Pro v4.1 — Ultra Edition", "b")
        self._log("   ✂️  NEW: Move File • ✏️ Rename File • 📁 Folder Tree", "c")
        if not DND_AVAILABLE:
            self._log("💡 pip install tkinterdnd2 for drag & drop", "o")

    # ══════════════════════════════════════════════════════
    #  QUEUE
    # ══════════════════════════════════════════════════════
    def _add_to_queue(self, paths):
        if self.engine:
            items = self.engine.scan_items(paths)
        else:
            items = []
            for p in paths:
                p = p.strip().strip("{}\"'")
                if os.path.isdir(p):
                    for root,dirs,files in os.walk(p):
                        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                        for f in files:
                            fp  = os.path.join(root,f)
                            rel = os.path.relpath(fp,os.path.dirname(p)).replace("\\","/")
                            items.append({"full_path":fp,"rel_path":rel,
                                          "size":os.path.getsize(fp),
                                          "ext":os.path.splitext(f)[1].lower() or ".file"})
                elif os.path.isfile(p):
                    fname = os.path.basename(p)
                    items.append({"full_path":p,"rel_path":fname,
                                  "size":os.path.getsize(p),
                                  "ext":os.path.splitext(fname)[1].lower() or ".file"})

        self.scanned_files.extend(items)
        for f in items:
            ic   = icon_for(f["ext"])
            ftyp = get_file_type(f["ext"])
            self.queue_tree.insert("","end",
                values=(ic,f["rel_path"],fmt_size(f["size"]),ftyp),
                tags=(ftyp,))
        self._refresh_stats()
        self._validate_upload()
        self.nb.select(0)

    def _refresh_stats(self):
        n  = len(self.scanned_files)
        sz = sum(f["size"] for f in self.scanned_files)
        tp = len({f["ext"] for f in self.scanned_files})
        self.stat_files.config(text=str(n))
        self.stat_size.config(text=fmt_size(sz))
        self.stat_types.config(text=str(tp))
        if n > 0:
            self.drop_outer.config(bg=C["green"])
            self.lbl_dz_icon.config(text="✅",fg=C["green"])
            self.lbl_dz_title.config(text=f"{n} item(s) queued")
            self.lbl_dz_sub.config(text=f"Total: {fmt_size(sz)} • {tp} types\nReady to upload →")
        else:
            self.drop_outer.config(bg=C["border_hi"])
            self.lbl_dz_icon.config(text="📥",fg=C["blue3"])
            self.lbl_dz_title.config(text="Drop Anything Here")
            self.lbl_dz_sub.config(
                text="Files • Folders • ZIP • Images • Videos • Audio • Code • Docs")

    def clear_queue(self):
        self.scanned_files = []
        for i in self.queue_tree.get_children():
            self.queue_tree.delete(i)
        self._refresh_stats(); self._validate_upload()

    def remove_from_queue(self):
        for sel in self.queue_tree.selection():
            vals = self.queue_tree.item(sel,"values")
            rel  = vals[1] if len(vals)>1 else ""
            self.scanned_files = [f for f in self.scanned_files
                                  if f["rel_path"]!=rel]
            self.queue_tree.delete(sel)
        self._refresh_stats(); self._validate_upload()

    def _q_ctx(self, e):
        try: self.q_menu.tk_popup(e.x_root,e.y_root)
        finally: self.q_menu.grab_release()

    def _rm_ctx(self, e):
        row = self.remote_tree.identify_row(e.y)
        if row: self.remote_tree.selection_set(row)
        try: self.rm_menu.tk_popup(e.x_root,e.y_root)
        finally: self.rm_menu.grab_release()

    # ══════════════════════════════════════════════════════
    #  BROWSE
    # ══════════════════════════════════════════════════════
    def browse_folder(self):
        p = filedialog.askdirectory(title="Select Folder")
        if p: self._add_to_queue([p])

    def browse_files(self):
        ps = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[("All Files","*.*")])
        if ps: self._add_to_queue(list(ps))

    def browse_zip(self):
        p = filedialog.askopenfilename(
            title="Select ZIP",
            filetypes=[("ZIP","*.zip"),("All","*.*")])
        if p: self._add_to_queue([p])

    def _dnd_enter(self, e):
        self.drop_outer.config(bg=C["blue1"])
        self.lbl_dz_icon.config(text="⬇️",fg=C["cyan"])
        self.lbl_dz_title.config(text="Drop it! ⚡",fg=C["cyan"])

    def _dnd_leave(self, e):
        self._refresh_stats()
        self.lbl_dz_title.config(fg=C["text"])

    def _dnd_drop(self, e):
        import re
        raw   = e.data.strip()
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        paths = [a or b for a,b in paths]
        self._add_to_queue(paths)

    # ══════════════════════════════════════════════════════
    #  GITHUB ACTIONS
    # ══════════════════════════════════════════════════════
    def do_connect(self):
        token = self.ent_token.get().strip()
        if not token:
            messagebox.showwarning("⚠️","Enter token!"); return
        self.btn_conn.config(text="⏳...", state="disabled")
        self.lbl_status.config(text="🟡 Connecting...", fg=C["orange"])
        def _w():
            try:
                eng  = GitHubEngine(token)
                user = eng.username
                self.root.after(0, lambda: self._on_connected(eng,token,user))
            except Exception as ex:
                self.root.after(0, lambda: self._on_conn_fail(str(ex)))
        threading.Thread(target=_w, daemon=True).start()

    def _on_connected(self, eng, token, user):
        self.engine = eng
        self.config["token"] = token
        self._save_cfg()
        self.btn_conn.config(text="✅ Connected", state="normal", bg=C["green"])
        self.lbl_status.config(text=f"🟢 @{user}", fg=C["green"])
        self._log(f"✅ Connected as @{user}", "g")
        self.do_refresh_repos()
        self._validate_upload()

    def _on_conn_fail(self, err):
        self.btn_conn.config(text="⚡  Connect to GitHub",
                            state="normal", bg=C["blue1"])
        self.lbl_status.config(text="🔴 Failed!", fg=C["red"])
        self._log(f"❌ {err}", "r")
        messagebox.showerror("Auth Failed", err)

    def do_refresh_repos(self):
        if not self.engine: return
        def _w():
            try:
                repos = self.engine.list_repos()
                self.root.after(0, lambda: self._on_repos(repos))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w, daemon=True).start()

    def _on_repos(self, repos):
        self.repos = repos
        display = [f"{'🔒' if r['private'] else '🌐'} {r['full_name']}"
                   for r in repos]
        self.repo_combo["values"] = display
        if display:
            self.repo_combo.current(0)
            self._on_repo_sel()
        self._log(f"📦 {len(repos)} repos loaded", "g")
        self._validate_upload()

    def _on_repo_sel(self, e=None):
        fn = self._get_repo()
        if not fn: return
        for r in self.repos:
            if r["full_name"] == fn:
                self.lbl_repo_info.config(
                    text=f"{'🔒' if r['private'] else '🌐'} "
                         f"{r['description'][:55] or 'No description'}")
                self.branch_combo.set(r["default_branch"])
                break
        def _w():
            try:
                brs = self.engine.list_branches(fn)
                self.root.after(0, lambda: self.branch_combo.config(values=brs))
            except: pass
        threading.Thread(target=_w, daemon=True).start()
        self._validate_upload()

    def do_create_repo(self):
        if not self.engine:
            messagebox.showwarning("⚠️","Connect first!"); return
        name = self.ent_newrepo.get().strip()
        if not name or name=="repo-name":
            messagebox.showwarning("⚠️","Enter repo name!"); return
        def _w():
            try:
                repo = self.engine.create_repo(name, private=self.priv_var.get())
                self.root.after(0, lambda: (
                    self._log(f"✅ Created: {repo.full_name}","g"),
                    self.do_refresh_repos()))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w, daemon=True).start()

    def do_create_branch(self):
        if not self.engine: return
        fn = self._get_repo()
        if not fn:
            messagebox.showwarning("⚠️","Select repo!"); return
        name = simpledialog.askstring("🌿 New Branch","Name:", parent=self.root)
        if not name: return
        src = self._get_branch()
        def _w():
            try:
                self.engine.create_branch(fn, name, src)
                brs = self.engine.list_branches(fn)
                self.root.after(0, lambda: (
                    self.branch_combo.config(values=brs),
                    self.branch_combo.set(name),
                    self._log(f"✅ Branch '{name}' created","g")))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w, daemon=True).start()

    # ── Upload ──
    def do_upload(self):
        if not self.engine or not self.scanned_files: return
        fn = self._get_repo()
        if not fn: return
        branch  = self._get_branch()
        commit  = self.ent_commit.get().strip() or "Upload files"
        target  = self.ent_target.get().strip()
        if "optional" in target: target=""
        n = len(self.scanned_files)
        if not messagebox.askyesno("🚀 Upload",
                                   f"Upload {n} file(s) → {fn} [{branch}]?"):
            return
        self.is_uploading = True
        self.btn_upload.config(state="disabled",text="⏳ UPLOADING...",bg=C["orange"])
        self.nb.select(2)
        self.p_uploaded.config(text="0"); self.p_total.config(text=str(n))
        self.p_size.config(text="—");    self.p_speed.config(text="—")
        self.lbl_pct.config(text="0%");  self.lbl_curfile.config(text="Starting...")
        self.pb_canvas.coords(self.pb_rect,0,0,0,14)
        self.pb_canvas.coords(self.pb_glow,0,0,0,14)
        self._log("═"*55,"H")
        self._log(f"🚀 Upload → {fn} [{branch}]","H")
        files_copy = list(self.scanned_files)
        def _w():
            def cb(ev,data):
                self.root.after(0, lambda: self._on_upload_ev(ev,data,fn))
            try:
                self.engine.upload_items(fn,files_copy,branch,commit,target,cb)
            except Exception as ex:
                self.root.after(0, lambda: self._on_upload_ev(
                    "fatal",{"error":str(ex)},fn))
        threading.Thread(target=_w, daemon=True).start()

    def _on_upload_ev(self, ev, data, repo):
        if ev=="start":
            self.p_total.config(text=str(data["total"]))
        elif ev=="uploading":
            f=data["file"]; ic=icon_for(os.path.splitext(f)[1])
            self.lbl_curfile.config(text=f"{ic}  {f}")
        elif ev=="progress":
            up=data["uploaded"]; tot=data["total"]
            b=data["bytes"];     spd=data.get("speed",0)
            pct=int(up/tot*100) if tot else 0
            self.p_uploaded.config(text=str(up))
            self.p_size.config(text=fmt_size(b))
            self.p_speed.config(text=f"{fmt_size(int(spd))}/s")
            self.lbl_pct.config(text=f"{pct}%")
            w=self.pb_canvas.winfo_width(); fw=int(w*pct/100)
            self.pb_canvas.coords(self.pb_rect,0,0,fw,14)
            self.pb_canvas.coords(self.pb_glow,max(0,fw-20),0,fw,14)
            f=data["file"]; ic=icon_for(os.path.splitext(f)[1])
            self._log(f"  ✅ {ic}  {f}  ({up}/{tot})","g")
        elif ev=="file_error":
            self._log(f"  ❌ {data['file']}: {data['error']}","r")
        elif ev=="done":
            up=data["uploaded"]; tot=data["total"]
            elapsed=data.get("elapsed",0)
            w=self.pb_canvas.winfo_width()
            self.pb_canvas.coords(self.pb_rect,0,0,w,14)
            self.pb_canvas.coords(self.pb_glow,max(0,w-30),0,w,14)
            self.lbl_pct.config(text="100% ✅")
            self.lbl_curfile.config(text="✨ Done!")
            self.p_elapsed.config(text=fmt_time(elapsed))
            self.is_uploading=False
            self.btn_upload.config(text="🚀  UPLOAD TO GITHUB",bg=C["blue1"])
            self._validate_upload()
            self._log(f"🎉 {up}/{tot} files uploaded in {fmt_time(elapsed)}","g")
            self._log("═"*55,"H")
            if messagebox.askyesno("🎉 Done!",
                                   f"✅ {up}/{tot} uploaded!\n\nOpen in browser?"):
                webbrowser.open(f"https://github.com/{repo}")
        elif ev=="fatal":
            self.is_uploading=False
            self.btn_upload.config(text="🚀  UPLOAD TO GITHUB",bg=C["blue1"])
            self._validate_upload()
            self._log(f"💥 {data['error']}","r")
            messagebox.showerror("Error",data["error"])

    # ── Remote File Manager ──
    def do_load_remote(self):
        fn = self._get_repo()
        if not fn or not self.engine:
            messagebox.showwarning("⚠️","Select repo & connect!"); return
        branch = self._get_branch()
        self._log(f"🔄 Loading remote files from {fn}...","b")
        def _w():
            try:
                files = self.engine.list_remote_files(fn, branch)
                self.root.after(0, lambda: self._on_remote(files))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w, daemon=True).start()

    def _on_remote(self, files):
        self.remote_files = files
        self._fill_remote(files)
        self._log(f"📄 {len(files)} remote files","g")

    def _fill_remote(self, files):
        for i in self.remote_tree.get_children():
            self.remote_tree.delete(i)
        for f in files:
            ext  = os.path.splitext(f["path"])[1].lower()
            ic   = icon_for(ext)
            ftyp = get_file_type(ext)
            self.remote_tree.insert("","end",
                values=(ic, f["path"], fmt_size(f["size"]),
                        f["sha"][:7] if f["sha"] else ""),
                tags=(ftyp,))

    def _filter_remote(self, e=None):
        q  = self.ent_search.get().lower()
        fs = [f for f in self.remote_files if q in f["path"].lower()]
        self._fill_remote(fs)

    def _selected_remote(self):
        sel = self.remote_tree.selection()
        if not sel:
            messagebox.showwarning("⚠️","Select a file first!"); return None,None
        vals = self.remote_tree.item(sel[0],"values")
        path = vals[1] if len(vals)>1 else ""
        for rf in self.remote_files:
            if rf["path"]==path: return rf["path"],rf["sha"]
        messagebox.showerror("Error",f"Not found: {path}")
        return None,None

    def do_edit_file(self):
        fn=self._get_repo()
        if not fn or not self.engine: return
        path,sha=self._selected_remote()
        if not path: return
        branch=self._get_branch()
        def _w():
            try:
                raw,cur_sha = self.engine.get_file(fn,path,branch)
                text = raw.decode("utf-8",errors="replace")
                self.root.after(0, lambda: self._editor(
                    fn,path,text,cur_sha,branch,edit=True))
            except Exception as ex:
                self.root.after(0, lambda: messagebox.showerror("Error",str(ex)))
        threading.Thread(target=_w, daemon=True).start()

    def _editor(self, fn, path, content, sha, branch, edit=True):
        ed=tk.Toplevel(self.root)
        ed.title(f"{'📝 Edit' if edit else '📄 Create'}: {path}")
        ed.geometry("900x650")
        ed.configure(bg=C["bg"])
        ed.transient(self.root); ed.grab_set()

        GradientFrame(ed,C["blue5"],C["cyan"],height=3,bg=C["bg"]).pack(fill="x")

        hdr=tk.Frame(ed,bg=C["card"],padx=16,pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr,text=f"{'📝' if edit else '📄'} {path}",
                font=("Segoe UI",11,"bold"),bg=C["card"],fg=C["text"]).pack(side="left")
        tk.Label(hdr,text=f"📦 {fn}  🌿 {branch}",
                font=("Segoe UI",9),bg=C["card"],fg=C["sub"]).pack(side="right")

        ef=tk.Frame(ed,bg=C["bg"])
        ef.pack(fill="both",expand=True,padx=8,pady=8)
        txt=tk.Text(ef,font=("Consolas",11),bg=C["input"],fg=C["text"],
                   insertbackground=C["cyan"],relief="flat",bd=8,wrap="none",undo=True,
                   selectbackground=C["blue2"])
        sx=ttk.Scrollbar(ef,orient="horizontal",command=txt.xview)
        sy=ttk.Scrollbar(ef,orient="vertical",  command=txt.yview)
        txt.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        sy.pack(side="right",fill="y"); sx.pack(side="bottom",fill="x")
        txt.pack(fill="both",expand=True)
        txt.insert("1.0",content)

        bot=tk.Frame(ed,bg=C["card"],padx=12,pady=8)
        bot.pack(fill="x")
        tk.Label(bot,text="💬",bg=C["card"],font=("Segoe UI",10)).pack(side="left")
        cm=tk.Entry(bot,font=("Segoe UI",10),bg=C["input"],fg=C["text"],
                   insertbackground=C["text"],relief="flat",bd=5)
        cm.pack(side="left",fill="x",expand=True,padx=8)
        cm.insert(0,f"{'Update' if edit else 'Create'} {path}")

        def _save():
            new=txt.get("1.0","end-1c"); msg=cm.get().strip() or f"Update {path}"
            def _w():
                try:
                    if edit: self.engine.update_file(fn,path,new,sha,branch,msg)
                    else:    self.engine.create_file_raw(fn,path,new,branch,msg)
                    self.root.after(0, lambda: (
                        self._log(f"✅ {'Updated' if edit else 'Created'}: {path}","g"),
                        ed.destroy(), self.do_load_remote()))
                except Exception as ex:
                    self.root.after(0, lambda: messagebox.showerror("Error",str(ex)))
            threading.Thread(target=_w,daemon=True).start()

        self._btn(bot,f"{'💾 Save & Push' if edit else '📄 Create & Push'}",
                 C["green"],_save,padx=16,pady=7).pack(side="right")
        self._btn(bot,"✖ Cancel",C["border"],ed.destroy,
                 padx=12,pady=7).pack(side="right",padx=(0,8))

    def do_delete_file(self):
        fn=self._get_repo()
        if not fn or not self.engine: return
        path,sha=self._selected_remote()
        if not path: return
        if not messagebox.askyesno("🗑️ Delete",
                                   f"Delete:\n{path}\n\nCannot be undone!"): return
        branch=self._get_branch()
        def _w():
            try:
                self.engine.delete_file(fn,path,sha,branch,
                                       f"Delete {path} via Uploader Pro")
                self.root.after(0, lambda: (
                    self._log(f"✅ Deleted: {path}","g"),
                    self.do_load_remote()))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    def do_create_file(self):
        fn=self._get_repo()
        if not fn or not self.engine:
            messagebox.showwarning("⚠️","Connect & select repo!"); return
        path=simpledialog.askstring("📄 Create File",
                                   "File path (e.g. src/hello.py):",
                                   parent=self.root)
        if not path: return
        self._editor(fn,path,"",None,self._get_branch(),edit=False)

    def do_create_folder(self):
        fn=self._get_repo()
        if not fn or not self.engine:
            messagebox.showwarning("⚠️","Connect & select repo!"); return
        folder=simpledialog.askstring("📁 Create Folder",
                                     "Folder path (e.g. src/utils):",
                                     parent=self.root)
        if not folder: return
        branch=self._get_branch()
        def _w():
            try:
                self.engine.create_folder(fn,folder,branch,
                                         f"Create folder {folder}")
                self.root.after(0, lambda: (
                    self._log(f"✅ Folder created: {folder}","g"),
                    self.do_load_remote()))
            except Exception as ex:
                self.root.after(0, lambda: self._log(f"❌ {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    # ══════════════════════════════════════════════════════
    #  ★★★  MOVE FILE  ★★★
    # ══════════════════════════════════════════════════════
    def do_move_file(self):
        fn = self._get_repo()
        if not fn or not self.engine:
            messagebox.showwarning("⚠️","Connect & select repo!"); return

        path, sha = self._selected_remote()
        if not path: return

        # Make sure we have remote files for folder tree
        if not self.remote_files:
            messagebox.showinfo("ℹ️","Load remote files first (🔄 Load button).")
            return

        # Open the beautiful move dialog
        dlg = MoveFileDialog(self.root, path, self.remote_files, C)

        if dlg.result is None:
            return  # User cancelled

        new_path   = dlg.result["new_path"]
        commit_msg = dlg.result["commit_msg"]
        branch     = self._get_branch()

        self._log(f"✂️  Moving: {path}","y")
        self._log(f"       → {new_path}","y")
        self.nb.select(2)

        def _w():
            try:
                self.engine.move_file(fn, path, new_path,
                                     branch, commit_msg)
                self.root.after(0, lambda: (
                    self._log(f"✅ Moved: {path} → {new_path}","g"),
                    self.do_load_remote()))
            except Exception as ex:
                self.root.after(0, lambda: (
                    self._log(f"❌ Move failed: {ex}","r"),
                    messagebox.showerror("Move Error", str(ex))))
        threading.Thread(target=_w, daemon=True).start()

    # ══════════════════════════════════════════════════════
    #  ★★★  RENAME FILE  ★★★
    # ══════════════════════════════════════════════════════
    def do_rename_file(self):
        fn = self._get_repo()
        if not fn or not self.engine:
            messagebox.showwarning("⚠️","Connect & select repo!"); return

        path, sha = self._selected_remote()
        if not path: return

        old_name = os.path.basename(path)
        new_name = simpledialog.askstring(
            "✏️ Rename File",
            f"Current name: {old_name}\n\nNew filename:",
            initialvalue=old_name,
            parent=self.root
        )

        if not new_name or new_name.strip() == old_name:
            return

        new_name   = new_name.strip()
        branch     = self._get_branch()
        commit_msg = f"Rename {old_name} → {new_name}"

        self._log(f"✏️  Renaming: {old_name} → {new_name}","y")

        def _w():
            try:
                new_path = self.engine.rename_file(fn, path, new_name,
                                                   branch, commit_msg)
                self.root.after(0, lambda: (
                    self._log(f"✅ Renamed → {new_path}","g"),
                    self.do_load_remote()))
            except Exception as ex:
                self.root.after(0, lambda: (
                    self._log(f"❌ Rename failed: {ex}","r"),
                    messagebox.showerror("Rename Error", str(ex))))
        threading.Thread(target=_w, daemon=True).start()


# ══════════════════════════════════════════════════════════════
#  LAUNCH
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║  🚀 GitHub Uploader Pro  ·  v4.1 Ultra Edition      ║
    ║  ✂️  Move File  •  ✏️ Rename  •  📁 Folder Tree     ║
    ╚══════════════════════════════════════════════════════╝
    """)
    App()