#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  GITHUB UPLOADER PRO — ULTRA v5.0                              ║
║  Tree Browser · Move · Rename · Delete · Upload · Premium UI   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, json, threading, webbrowser, time, zipfile, tempfile, re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ── auto-install ──────────────────────────────────────────────
def _pip(pkg):
    import subprocess
    subprocess.check_call([sys.executable,"-m","pip","install",pkg],
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    from github import Github, GithubException
except ImportError:
    _pip("PyGithub"); from github import Github, GithubException

DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD; DND = True
except ImportError:
    pass

CFG = os.path.join(os.path.expanduser("~"),".ghup_v5.json")

# ══════════════════════════════════════════════════════════════
#  PALETTE  — teal · navy · green gradients, rounded feel
# ══════════════════════════════════════════════════════════════
P = {
    "bg":       "#070b14",
    "bg2":      "#0b1120",
    "sidebar":  "#090e1c",
    "card":     "#0f1729",
    "card2":    "#131d33",
    "input":    "#080d1a",
    "border":   "#1b2640",
    "bhi":      "#243560",
    "text":     "#dce8ff",
    "sub":      "#7a9bbf",
    "muted":    "#3a5070",
    # accents
    "teal":     "#00d4aa",
    "teal2":    "#00b894",
    "navy":     "#1a56db",
    "navy2":    "#1e40af",
    "green":    "#00e676",
    "green2":   "#00c853",
    "purple":   "#845ef7",
    "purple2":  "#6741d9",
    "amber":    "#ffca28",
    "red":      "#ff4757",
    "cyan":     "#00cfe8",
    "rose":     "#f43f5e",
}

SKIP = {'.git','__pycache__','node_modules','.DS_Store','Thumbs.db',
        '.vscode','.idea','dist','build','.pytest_cache','venv',
        '.venv','env','.tox','.mypy_cache','.eggs'}

FICONS = {
    '.py':'PY','.js':'JS','.ts':'TS','.html':'HTML','.css':'CSS',
    '.json':'JSON','.md':'MD','.txt':'TXT','.yml':'YML','.yaml':'YML',
    '.xml':'XML','.sql':'SQL','.sh':'SH','.bat':'BAT',
    '.png':'IMG','.jpg':'IMG','.jpeg':'IMG','.gif':'GIF','.svg':'SVG',
    '.webp':'IMG','.ico':'ICO',
    '.mp4':'MP4','.avi':'AVI','.mov':'MOV','.mkv':'MKV',
    '.mp3':'MP3','.wav':'WAV','.flac':'FLAC','.aac':'AAC',
    '.zip':'ZIP','.rar':'RAR','.tar':'TAR','.gz':'GZ','.7z':'7Z',
    '.java':'JAVA','.cpp':'CPP','.c':'C','.h':'H','.go':'GO',
    '.rs':'RS','.php':'PHP','.dart':'DART','.vue':'VUE',
    '.jsx':'JSX','.tsx':'TSX','.rb':'RB','.swift':'SWIFT',
    '.kt':'KT','.pdf':'PDF','.doc':'DOC','.docx':'DOCX',
    '.xls':'XLS','.xlsx':'XLSX','.csv':'CSV',
    '.toml':'TOML','.ini':'INI','.lock':'LOCK','.env':'ENV',
    '.gitignore':'GIT','.dockerfile':'DOCK','.wasm':'WASM',
    '.exe':'EXE','.dll':'DLL',
}

FCOLORS = {
    '.py':'#4fc3f7','.js':'#ffd54f','.ts':'#4dd0e1',
    '.html':'#ff8a65','.css':'#f06292','.json':'#aed581',
    '.md':'#80cbc4','.txt':'#b0bec5','.vue':'#a5d6a7',
    '.jsx':'#4fc3f7','.tsx':'#4dd0e1','.go':'#4fc3f7',
    '.rs':'#ff8a65','.java':'#ffcc02','.php':'#ce93d8',
    '.png':'#ba68c8','.jpg':'#ba68c8','.jpeg':'#ba68c8',
    '.gif':'#f48fb1','.svg':'#80deea',
    '.mp4':'#ef9a9a','.mp3':'#f48fb1','.wav':'#f48fb1',
    '.zip':'#ffb74d','.rar':'#ffb74d','.tar':'#ffb74d',
    '.pdf':'#ef5350','.doc':'#42a5f5','.xls':'#66bb6a',
}

def fext(path): return os.path.splitext(path)[1].lower()
def flabel(path):
    e=fext(path); return FICONS.get(e, os.path.splitext(path)[1][1:].upper()[:5] or "FILE")
def fcolor(path):
    return FCOLORS.get(fext(path), P["sub"])
def fmt_size(b):
    if b<1024: return f"{b} B"
    if b<1<<20: return f"{b/1024:.1f} KB"
    if b<1<<30: return f"{b/(1<<20):.1f} MB"
    return f"{b/(1<<30):.1f} GB"
def fmt_time(s):
    if s<60: return f"{s:.1f}s"
    return f"{s/60:.1f}m"

# ══════════════════════════════════════════════════════════════
#  ROUNDED-RECT CANVAS HELPER
# ══════════════════════════════════════════════════════════════
def rounded_rect(canvas, x1,y1,x2,y2, r=10, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
           x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)

class GradBar(tk.Canvas):
    def __init__(self, p, c1, c2, h=3, **kw):
        super().__init__(p, height=h, highlightthickness=0, **kw)
        self.c1,self.c2=c1,c2
        self.bind("<Configure>",self._draw)
    def _draw(self,e=None):
        self.delete("all"); w=self.winfo_width(); h=self.winfo_height()
        if w<2: return
        r1,g1,b1=self.winfo_rgb(self.c1)
        r2,g2,b2=self.winfo_rgb(self.c2)
        for i in range(w):
            r=int(r1+(r2-r1)*i/w)>>8
            g=int(g1+(g2-g1)*i/w)>>8
            b=int(b1+(b2-b1)*i/w)>>8
            self.create_line(i,0,i,h,fill=f"#{r:02x}{g:02x}{b:02x}")

# ══════════════════════════════════════════════════════════════
#  CUSTOM BADGE LABEL  (rounded bg)
# ══════════════════════════════════════════════════════════════
class Badge(tk.Canvas):
    def __init__(self, parent, text, fg="#fff", bg=P["navy"], r=6, **kw):
        f=("Segoe UI",8,"bold")
        tmp=tk.Label(parent,text=text,font=f); w=tmp.winfo_reqwidth()+16; h=20
        tmp.destroy()
        super().__init__(parent,width=w,height=h,
                        highlightthickness=0,bg=parent["bg"],**kw)
        rounded_rect(self,1,1,w-1,h-1,r=r,fill=bg,outline="")
        self.create_text(w//2,h//2,text=text,fill=fg,font=f)

# ══════════════════════════════════════════════════════════════
#  TOOLTIP
# ══════════════════════════════════════════════════════════════
class Tip:
    def __init__(self,w,t):
        self.w=w;self.t=t;self.tip=None
        w.bind("<Enter>",self.show);w.bind("<Leave>",self.hide)
    def show(self,e=None):
        if self.tip: return
        x=self.w.winfo_rootx()+16; y=self.w.winfo_rooty()+self.w.winfo_height()+4
        self.tip=tw=tk.Toplevel(self.w)
        tw.wm_overrideredirect(True); tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost",True)
        f=tk.Frame(tw,bg=P["bhi"],bd=1); f.pack()
        tk.Label(f,text=self.t,bg=P["card2"],fg=P["text"],
                font=("Segoe UI",9),padx=10,pady=5).pack()
    def hide(self,e=None):
        if self.tip: self.tip.destroy(); self.tip=None

# ══════════════════════════════════════════════════════════════
#  GITHUB ENGINE
# ══════════════════════════════════════════════════════════════
class Engine:
    def __init__(self, token):
        self.gh   = Github(token, per_page=100)
        self.user = self.gh.get_user()

    @property
    def username(self): return self.user.login

    def list_repos(self):
        return [{"full_name":r.full_name,"name":r.name,"private":r.private,
                 "default_branch":r.default_branch,"description":r.description or "",
                 "stars":r.stargazers_count,"lang":r.language or ""}
                for r in self.user.get_repos(affiliation="owner",sort="updated")]

    def create_repo(self, name, private=False):
        return self.user.create_repo(name=name,private=private,auto_init=True)

    def list_branches(self, fn):
        return [b.name for b in self.gh.get_repo(fn).get_branches()]

    def create_branch(self, fn, new, src):
        repo=self.gh.get_repo(fn)
        repo.create_git_ref(f"refs/heads/{new}",
                           repo.get_branch(src).commit.sha)

    # ── Remote tree ──
    def list_remote_tree(self, fn, branch):
        """Returns flat list + folder set"""
        repo=self.gh.get_repo(fn)
        files=[]; folders=set()
        self._recurse(repo,"",branch,files,folders)
        return files, folders

    def _recurse(self, repo, path, branch, files, folders):
        try:
            items=repo.get_contents(path,ref=branch)
            if not isinstance(items,list): items=[items]
            for c in items:
                if c.type=="dir":
                    folders.add(c.path)
                    self._recurse(repo,c.path,branch,files,folders)
                else:
                    files.append({"path":c.path,"sha":c.sha,
                                  "size":c.size,"url":c.download_url})
        except: pass

    # ── File CRUD ──
    def read_file(self, fn, path, branch):
        c=self.gh.get_repo(fn).get_contents(path,ref=branch)
        return c.decoded_content, c.sha

    def write_file(self, fn, path, content, sha, branch, msg):
        repo=self.gh.get_repo(fn)
        if isinstance(content,str): content=content.encode()
        if sha:
            repo.update_file(path,msg,content,sha,branch=branch)
        else:
            repo.create_file(path,msg,content,branch=branch)

    def delete_file(self, fn, path, sha, branch, msg):
        self.gh.get_repo(fn).delete_file(path,msg,sha,branch=branch)

    def create_folder(self, fn, folder, branch, msg):
        self.gh.get_repo(fn).create_file(
            folder.rstrip("/")+  "/.gitkeep",msg,b"",branch=branch)

    # ── Move / Rename ──
    def move_file(self, fn, src, dst, branch, msg):
        repo=self.gh.get_repo(fn)
        obj=repo.get_contents(src,ref=branch)
        raw=obj.decoded_content; src_sha=obj.sha
        # create at dst
        try:
            dst_obj=repo.get_contents(dst,ref=branch)
            repo.update_file(dst,msg+" (overwrite)",raw,dst_obj.sha,branch=branch)
        except:
            repo.create_file(dst,msg+" (create)",raw,branch=branch)
        # delete src
        repo.delete_file(src,msg+" (remove src)",src_sha,branch=branch)

    # ── SHA map ──
    def sha_map(self, fn, branch):
        files,_=self.list_remote_tree(fn,branch)
        return {f["path"]:f["sha"] for f in files}

    # ── Scan local ──
    def scan(self, paths):
        result=[]
        for p in paths:
            p=p.strip().strip("{}\"'")
            if not os.path.exists(p): continue
            if os.path.isdir(p):
                self._scan_dir(p,os.path.basename(p),result)
            elif p.lower().endswith(".zip"):
                tmp=tempfile.mkdtemp()
                try:
                    with zipfile.ZipFile(p) as z: z.extractall(tmp)
                    self._scan_dir(tmp,
                        os.path.splitext(os.path.basename(p))[0],result)
                except: pass
            elif os.path.isfile(p):
                fname=os.path.basename(p)
                result.append({"full_path":p,"rel_path":fname,
                               "size":os.path.getsize(p),
                               "ext":fext(p)})
        return result

    def _scan_dir(self, base, prefix, result):
        parent=os.path.dirname(base)
        for root,dirs,files in os.walk(base):
            dirs[:]=[d for d in dirs if d not in SKIP]
            for f in files:
                if f in SKIP: continue
                fp=os.path.join(root,f)
                rel=os.path.relpath(fp,parent).replace("\\","/")
                result.append({"full_path":fp,"rel_path":rel,
                               "size":os.path.getsize(fp),"ext":fext(fp)})

    # ── Upload ──
    def upload(self, fn, items, branch, commit, target="", cb=None):
        repo=self.gh.get_repo(fn)
        sm=self.sha_map(fn,branch)
        total=len(items); done=0; tbytes=0; errs=[]; t0=time.time()
        if cb: cb("start",{"total":total})
        for i,f in enumerate(items):
            rel=f["rel_path"]
            if target: rel=target.strip("/")+"/"+rel
            try:
                with open(f["full_path"],"rb") as fh: content=fh.read()
                if cb: cb("uploading",{"file":rel,"index":i+1,"total":total})
                if rel in sm:
                    repo.update_file(rel,f"{commit} - update {rel}",
                                    content,sm[rel],branch=branch)
                else:
                    repo.create_file(rel,f"{commit} - add {rel}",
                                    content,branch=branch)
                done+=1; tbytes+=f["size"]
                spd=tbytes/(time.time()-t0+0.001)
                if cb: cb("progress",{"file":rel,"uploaded":done,"total":total,
                                      "bytes":tbytes,"speed":spd})
            except Exception as e:
                errs.append({"file":rel,"error":str(e)})
                if cb: cb("file_error",{"file":rel,"error":str(e)})
        elapsed=time.time()-t0
        if cb: cb("done",{"uploaded":done,"total":total,
                          "bytes":tbytes,"errors":errs,"elapsed":elapsed})

# ══════════════════════════════════════════════════════════════
#  REMOTE FILE TREE (Tab 2)
# ══════════════════════════════════════════════════════════════
class RemoteTreePanel(tk.Frame):
    """
    Left: folder tree   Right: files in selected folder
    Full CRUD on both panes.
    """
    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg=P["bg"], **kw)
        self.app=app
        self._all_files=[]
        self._all_folders=set()
        self._cur_folder=""   # "" = root
        self._build()

    def _build(self):
        # Toolbar
        tb=tk.Frame(self, bg=P["card2"])
        tb.pack(fill="x", padx=10, pady=(8,4))

        self._ibtn(tb,"Load Tree",P["navy"],self.do_load,
                  tip="Reload folder & file list from GitHub")
        self._ibtn(tb,"New File",P["green2"],self.do_new_file,
                  tip="Create new file in selected folder")
        self._ibtn(tb,"New Folder",P["teal"],self.do_new_folder,
                  tip="Create new folder in repository")
        self._ibtn(tb,"Upload Here",P["purple"],self.do_upload_here,
                  tip="Upload local files into selected folder")

        # search
        sw=tk.Frame(tb,bg=P["border"]); sw.pack(side="right",padx=(0,4))
        si=tk.Frame(sw,bg=P["input"]); si.pack(fill="x",padx=1,pady=1)
        tk.Label(si,text="Search",bg=P["input"],fg=P["muted"],
                font=("Segoe UI",8)).pack(side="left",padx=(8,2))
        self.ent_search=tk.Entry(si,font=("Segoe UI",9),bg=P["input"],
                                 fg=P["text"],insertbackground=P["text"],
                                 relief="flat",bd=4,width=18)
        self.ent_search.pack(padx=(0,6),pady=3)
        self.ent_search.bind("<KeyRelease>",self._on_search)

        # PanedWindow
        pane=tk.PanedWindow(self,orient="horizontal",
                           bg=P["bg"],sashwidth=5,sashpad=0,
                           sashrelief="flat")
        pane.pack(fill="both",expand=True,padx=10,pady=(0,10))

        # ── LEFT: Folder tree ──────────────────────────
        left=tk.Frame(pane,bg=P["bg"])
        pane.add(left,width=240,minsize=180)

        lh=tk.Frame(left,bg=P["card2"])
        lh.pack(fill="x",pady=(0,3))
        tk.Label(lh,text="Folders",
                font=("Segoe UI",9,"bold"),
                bg=P["card2"],fg=P["teal"]).pack(side="left",padx=10,pady=7)

        style=ttk.Style()
        style.configure("FTree.Treeview",
                        background=P["input"],foreground=P["text"],
                        fieldbackground=P["input"],borderwidth=0,
                        font=("Segoe UI",10),rowheight=26)
        style.map("FTree.Treeview",
                  background=[("selected",P["navy2"])])
        style.configure("FTree.Treeview.Heading",
                        background=P["card2"],foreground=P["teal"],
                        font=("Segoe UI",9,"bold"),relief="flat")

        ft=tk.Frame(left,bg=P["bg"])
        ft.pack(fill="both",expand=True)
        self.ftree=ttk.Treeview(ft,columns=("name",),show="tree headings",
                                style="FTree.Treeview",selectmode="browse")
        self.ftree.heading("name",text="Folder")
        self.ftree.column("#0",width=22,minwidth=22)
        self.ftree.column("name",width=190)
        fts=ttk.Scrollbar(ft,orient="vertical",command=self.ftree.yview)
        self.ftree.configure(yscrollcommand=fts.set)
        fts.pack(side="right",fill="y")
        self.ftree.pack(fill="both",expand=True)
        self.ftree.tag_configure("folder",foreground=P["teal"])
        self.ftree.tag_configure("root",  foreground=P["amber"])
        self.ftree.bind("<<TreeviewSelect>>",self._on_folder_sel)

        # ── RIGHT: File list ───────────────────────────
        right=tk.Frame(pane,bg=P["bg"])
        pane.add(right,minsize=300)

        rh=tk.Frame(right,bg=P["card2"])
        rh.pack(fill="x",pady=(0,3))
        self.lbl_cur=tk.Label(rh,text="/ (root)",
                             font=("Segoe UI",10,"bold"),
                             bg=P["card2"],fg=P["text"])
        self.lbl_cur.pack(side="left",padx=10,pady=7)
        self.lbl_count=tk.Label(rh,text="",
                               font=("Segoe UI",8),
                               bg=P["card2"],fg=P["muted"])
        self.lbl_count.pack(side="right",padx=10)

        # File action buttons
        ab=tk.Frame(right,bg=P["bg"])
        ab.pack(fill="x",pady=(0,3))
        self._ibtn(ab,"Edit",P["navy"],self.do_edit,
                  tip="Edit selected file content")
        self._ibtn(ab,"Move",P["purple2"],self.do_move,
                  tip="Move file to another folder")
        self._ibtn(ab,"Rename",P["teal2"],self.do_rename,
                  tip="Rename selected file")
        self._ibtn(ab,"Delete",P["red"],self.do_delete,
                  tip="Delete selected file permanently")
        self._ibtn(ab,"Move Out",P["amber"],self.do_move_out,
                  tip="Move file to parent folder")

        style2=ttk.Style()
        style2.configure("FList.Treeview",
                         background=P["input"],foreground=P["text"],
                         fieldbackground=P["input"],borderwidth=0,
                         font=("Consolas",9),rowheight=24)
        style2.map("FList.Treeview",
                   background=[("selected",P["navy2"])])
        style2.configure("FList.Treeview.Heading",
                         background=P["card2"],foreground=P["teal"],
                         font=("Segoe UI",9,"bold"),relief="flat")

        lf=tk.Frame(right,bg=P["bg"])
        lf.pack(fill="both",expand=True)

        self.flist=ttk.Treeview(lf,
                                columns=("badge","name","size","path"),
                                show="headings",style="FList.Treeview",
                                selectmode="browse")
        self.flist.heading("badge",text="Type")
        self.flist.heading("name", text="Filename")
        self.flist.heading("size", text="Size")
        self.flist.heading("path", text="Full Path")
        self.flist.column("badge",width=60, anchor="center")
        self.flist.column("name", width=220)
        self.flist.column("size", width=80, anchor="e")
        self.flist.column("path", width=300)

        ls=ttk.Scrollbar(lf,orient="vertical",command=self.flist.yview)
        self.flist.configure(yscrollcommand=ls.set)
        ls.pack(side="right",fill="y")
        self.flist.pack(fill="both",expand=True)
        self.flist.bind("<Double-1>",lambda e:self.do_edit())

        # Context menu
        self.ctx=tk.Menu(self,tearoff=0,bg=P["card"],fg=P["text"],
                        activebackground=P["navy2"],
                        font=("Segoe UI",9))
        self.ctx.add_command(label="Edit File",     command=self.do_edit)
        self.ctx.add_command(label="Move to Folder",command=self.do_move)
        self.ctx.add_command(label="Rename",        command=self.do_rename)
        self.ctx.add_command(label="Move Out",      command=self.do_move_out)
        self.ctx.add_separator()
        self.ctx.add_command(label="Delete",        command=self.do_delete)
        self.flist.bind("<Button-3>",self._ctx_menu)

    # ── helpers ──
    def _ibtn(self, parent, text, bg, cmd, tip=""):
        b=tk.Button(parent,text=text,bg=bg,fg="#ffffff",
                   font=("Segoe UI",9,"bold"),relief="flat",
                   padx=12,pady=6,cursor="hand2",
                   activebackground=bg,activeforeground="#fff",
                   command=cmd)
        b.pack(side="left",padx=(0,3),pady=6)
        if tip: Tip(b,tip)
        return b

    def _ctx_menu(self,e):
        row=self.flist.identify_row(e.y)
        if row: self.flist.selection_set(row)
        try: self.ctx.tk_popup(e.x_root,e.y_root)
        finally: self.ctx.grab_release()

    def _fn(self): return self.app._get_repo()
    def _br(self): return self.app._get_branch()
    def _log(self,m,t="m"): self.app._log(m,t)

    # ── load ──
    def do_load(self):
        fn=self._fn()
        if not fn or not self.app.engine:
            messagebox.showwarning("Warning","Connect and select a repository first.")
            return
        self._log(f"Loading remote tree from {fn} ...","b")
        def _w():
            try:
                files,folders=self.app.engine.list_remote_tree(fn,self._br())
                self.app.root.after(0,lambda:self._on_loaded(files,folders))
            except Exception as ex:
                self.app.root.after(0,lambda:self._log(f"Error: {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    def _on_loaded(self,files,folders):
        self._all_files=files
        self._all_folders=folders
        self._build_folder_tree()
        self._show_folder("")
        self._log(f"Loaded {len(files)} files, {len(folders)} folders","g")

    def _build_folder_tree(self):
        for i in self.ftree.get_children(): self.ftree.delete(i)
        # root
        rid=self.ftree.insert("","end",values=("  /  root",),
                             text="",open=True,tags=("root",))
        self._folder_ids={"":rid}
        for folder in sorted(self._all_folders):
            parts=folder.split("/")
            parent=""
            for i,part in enumerate(parts):
                cp="/".join(parts[:i+1])
                if cp not in self._folder_ids:
                    pid=self._folder_ids.get(parent,rid)
                    name="  "+("  "*i)+" "+part
                    fid=self.ftree.insert(pid,"end",
                                         values=(name,),text="",
                                         tags=("folder",),open=False)
                    self._folder_ids[cp]=fid
                parent=cp

    def _show_folder(self, folder_path):
        self._cur_folder=folder_path
        label="/ root" if not folder_path else f"/ {folder_path}"
        self.lbl_cur.config(text=label)

        # files directly inside this folder
        files=[]
        for f in self._all_files:
            fp=f["path"]
            if folder_path=="":
                # root = files with no slash
                if "/" not in fp: files.append(f)
            else:
                prefix=folder_path+"/"
                if fp.startswith(prefix):
                    remainder=fp[len(prefix):]
                    if "/" not in remainder:   # direct children only
                        files.append(f)

        for i in self.flist.get_children(): self.flist.delete(i)
        for f in files:
            fname=os.path.basename(f["path"])
            badge=flabel(f["path"])
            col=fcolor(f["path"])
            iid=self.flist.insert("","end",
                values=(badge,fname,fmt_size(f["size"]),f["path"]),
                tags=(badge,))
            self.flist.tag_configure(badge,foreground=col)

        self.lbl_count.config(text=f"{len(files)} file(s)")

    def _on_folder_sel(self,e=None):
        sel=self.ftree.selection()
        if not sel: return
        # find path from id
        fid=sel[0]
        for path,pid in self._folder_ids.items():
            if pid==fid:
                self._show_folder(path)
                return

    def _on_search(self,e=None):
        q=self.ent_search.get().lower()
        if not q:
            self._show_folder(self._cur_folder); return
        for i in self.flist.get_children(): self.flist.delete(i)
        for f in self._all_files:
            if q in f["path"].lower():
                fname=os.path.basename(f["path"])
                badge=flabel(f["path"]); col=fcolor(f["path"])
                self.flist.insert("","end",
                    values=(badge,fname,fmt_size(f["size"]),f["path"]),
                    tags=(badge,))
                self.flist.tag_configure(badge,foreground=col)

    # ── selected file ──
    def _sel(self):
        sel=self.flist.selection()
        if not sel:
            messagebox.showwarning("Warning","Select a file first."); return None
        vals=self.flist.item(sel[0],"values")
        path=vals[3] if len(vals)>3 else ""
        for rf in self._all_files:
            if rf["path"]==path: return rf
        messagebox.showerror("Error",f"File not found: {path}"); return None

    # ── EDIT ──
    def do_edit(self):
        rf=self._sel()
        if not rf: return
        fn=self._fn(); br=self._br()
        self._log(f"Loading {rf['path']} ...","b")
        def _w():
            try:
                raw,sha=self.app.engine.read_file(fn,rf["path"],br)
                text=raw.decode("utf-8",errors="replace")
                self.app.root.after(0,lambda:self._open_editor(
                    fn,rf["path"],text,sha,br))
            except Exception as ex:
                self.app.root.after(0,lambda:messagebox.showerror("Error",str(ex)))
        threading.Thread(target=_w,daemon=True).start()

    def _open_editor(self,fn,path,content,sha,branch):
        ed=tk.Toplevel(self.app.root)
        ed.title(f"Edit  —  {path}")
        ed.geometry("950x680"); ed.configure(bg=P["bg"])
        ed.transient(self.app.root); ed.grab_set()

        GradBar(ed,P["teal"],P["navy"],h=3,bg=P["bg"]).pack(fill="x")

        hdr=tk.Frame(ed,bg=P["card"],padx=16,pady=10); hdr.pack(fill="x")
        tk.Label(hdr,text="Edit File",font=("Segoe UI",12,"bold"),
                bg=P["card"],fg=P["text"]).pack(side="left")
        tk.Label(hdr,text=path,font=("Consolas",10),
                bg=P["card"],fg=P["teal"]).pack(side="left",padx=12)
        tk.Label(hdr,text=f"{fn}  •  {branch}",font=("Segoe UI",9),
                bg=P["card"],fg=P["sub"]).pack(side="right")

        ef=tk.Frame(ed,bg=P["bg"]); ef.pack(fill="both",expand=True,padx=8,pady=8)

        # line numbers
        lnf=tk.Frame(ef,bg=P["input"]); lnf.pack(side="left",fill="y")
        ln=tk.Text(lnf,width=4,font=("Consolas",11),bg=P["input"],
                  fg=P["muted"],relief="flat",bd=8,state="disabled",
                  selectbackground=P["input"])
        ln.pack(fill="y",expand=True)

        txt=tk.Text(ef,font=("Consolas",11),bg=P["input"],fg=P["text"],
                   insertbackground=P["teal"],relief="flat",bd=8,
                   wrap="none",undo=True,selectbackground=P["navy2"])
        sx=ttk.Scrollbar(ef,orient="horizontal",command=txt.xview)
        sy=ttk.Scrollbar(ef,orient="vertical",  command=txt.yview)
        txt.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        sy.pack(side="right",fill="y"); sx.pack(side="bottom",fill="x")
        txt.pack(fill="both",expand=True)
        txt.insert("1.0",content)

        def _update_ln(e=None):
            ln.config(state="normal"); ln.delete("1.0","end")
            lines=int(txt.index("end-1c").split(".")[0])
            ln.insert("1.0","\n".join(str(i) for i in range(1,lines+1)))
            ln.config(state="disabled")
        txt.bind("<KeyRelease>",_update_ln); _update_ln()

        bot=tk.Frame(ed,bg=P["card"],padx=12,pady=8); bot.pack(fill="x")
        tk.Label(bot,text="Commit",font=("Segoe UI",9),
                bg=P["card"],fg=P["sub"]).pack(side="left")
        cm=tk.Entry(bot,font=("Segoe UI",10),bg=P["input"],fg=P["text"],
                   insertbackground=P["text"],relief="flat",bd=5)
        cm.pack(side="left",fill="x",expand=True,padx=8)
        cm.insert(0,f"Edit {os.path.basename(path)}")

        def _save():
            new=txt.get("1.0","end-1c"); msg=cm.get().strip() or f"Edit {path}"
            def _w():
                try:
                    self.app.engine.write_file(fn,path,new,sha,branch,msg)
                    self.app.root.after(0,lambda:(
                        self._log(f"Saved: {path}","g"),
                        ed.destroy(), self.do_load()))
                except Exception as ex:
                    self.app.root.after(0,lambda:messagebox.showerror("Error",str(ex)))
            threading.Thread(target=_w,daemon=True).start()

        tk.Button(bot,text="Save & Push",bg=P["green2"],fg="#fff",
                 font=("Segoe UI",10,"bold"),relief="flat",padx=16,pady=6,
                 cursor="hand2",command=_save).pack(side="right")
        tk.Button(bot,text="Cancel",bg=P["border"],fg=P["text"],
                 font=("Segoe UI",10),relief="flat",padx=12,pady=6,
                 cursor="hand2",command=ed.destroy).pack(side="right",padx=(0,6))

    # ── MOVE ──
    def do_move(self):
        rf=self._sel()
        if not rf: return
        fn=self._fn(); br=self._br()

        # Pick destination from folder list
        folders=sorted(self._all_folders)
        choices=["/ (root)"]+[f for f in folders]

        dlg=tk.Toplevel(self.app.root)
        dlg.title("Move File"); dlg.geometry("480x420")
        dlg.configure(bg=P["bg"]); dlg.transient(self.app.root); dlg.grab_set()

        GradBar(dlg,P["teal"],P["purple"],h=3,bg=P["bg"]).pack(fill="x")

        hdr=tk.Frame(dlg,bg=P["card"],padx=14,pady=10); hdr.pack(fill="x")
        tk.Label(hdr,text="Move File",font=("Segoe UI",12,"bold"),
                bg=P["card"],fg=P["text"]).pack(side="left")
        tk.Label(hdr,text=f"Moving:  {rf['path']}",
                font=("Consolas",9),bg=P["card"],fg=P["teal"]).pack(anchor="w",padx=14,pady=4)

        body=tk.Frame(dlg,bg=P["bg"]); body.pack(fill="both",expand=True,padx=12,pady=8)

        tk.Label(body,text="Select destination folder:",
                font=("Segoe UI",10,"bold"),
                bg=P["bg"],fg=P["sub"]).pack(anchor="w",pady=(0,6))

        lb_frame=tk.Frame(body,bg=P["border"]); lb_frame.pack(fill="both",expand=True)
        lb_in=tk.Frame(lb_frame,bg=P["input"]); lb_in.pack(fill="both",expand=True,padx=1,pady=1)

        lb=tk.Listbox(lb_in,font=("Segoe UI",10),bg=P["input"],fg=P["text"],
                     selectbackground=P["navy2"],selectforeground="#fff",
                     relief="flat",bd=0,activestyle="none")
        lbs=ttk.Scrollbar(lb_in,orient="vertical",command=lb.yview)
        lb.configure(yscrollcommand=lbs.set)
        lbs.pack(side="right",fill="y"); lb.pack(fill="both",expand=True)
        for c in choices: lb.insert("end",c)
        lb.selection_set(0)

        # filename override
        fn_row=tk.Frame(body,bg=P["bg"]); fn_row.pack(fill="x",pady=(8,0))
        tk.Label(fn_row,text="New filename (optional):",
                font=("Segoe UI",9),bg=P["bg"],fg=P["sub"]).pack(anchor="w")
        fn_e=tk.Entry(fn_row,font=("Consolas",10),bg=P["input"],fg=P["text"],
                     insertbackground=P["text"],relief="flat",bd=6)
        fn_e.pack(fill="x",pady=(3,0))
        fn_e.insert(0,os.path.basename(rf["path"]))

        # commit
        cm_row=tk.Frame(body,bg=P["bg"]); cm_row.pack(fill="x",pady=(8,0))
        tk.Label(cm_row,text="Commit message:",
                font=("Segoe UI",9),bg=P["bg"],fg=P["sub"]).pack(anchor="w")
        cm_e=tk.Entry(cm_row,font=("Segoe UI",9),bg=P["input"],fg=P["text"],
                     insertbackground=P["text"],relief="flat",bd=6)
        cm_e.pack(fill="x",pady=(3,0))
        cm_e.insert(0,f"Move {os.path.basename(rf['path'])}")

        result={"ok":False}
        def _ok():
            sel=lb.curselection()
            dest_folder="" if not sel or lb.get(sel[0])=="/ (root)" else lb.get(sel[0])
            new_name=fn_e.get().strip() or os.path.basename(rf["path"])
            dst=new_name if not dest_folder else dest_folder+"/"+new_name
            result.update({"ok":True,"dst":dst,"msg":cm_e.get().strip()
                           or f"Move to {dst}"})
            dlg.destroy()

        bot=tk.Frame(dlg,bg=P["card"],padx=12,pady=8); bot.pack(fill="x")
        tk.Button(bot,text="Move File",bg=P["purple2"],fg="#fff",
                 font=("Segoe UI",10,"bold"),relief="flat",
                 padx=16,pady=6,cursor="hand2",command=_ok).pack(side="right")
        tk.Button(bot,text="Cancel",bg=P["border"],fg=P["text"],
                 font=("Segoe UI",10),relief="flat",
                 padx=12,pady=6,cursor="hand2",command=dlg.destroy).pack(
                 side="right",padx=(0,6))
        dlg.wait_window()

        if not result["ok"]: return
        dst=result["dst"]; msg=result["msg"]
        if dst==rf["path"]: return

        self._log(f"Moving  {rf['path']}  →  {dst}","y")
        def _w():
            try:
                self.app.engine.move_file(fn,rf["path"],dst,br,msg)
                self.app.root.after(0,lambda:(
                    self._log(f"Moved  →  {dst}","g"),
                    self.do_load()))
            except Exception as ex:
                self.app.root.after(0,lambda:(
                    self._log(f"Error: {ex}","r"),
                    messagebox.showerror("Error",str(ex))))
        threading.Thread(target=_w,daemon=True).start()

    # ── MOVE OUT (to parent) ──
    def do_move_out(self):
        rf=self._sel()
        if not rf: return
        fn=self._fn(); br=self._br()
        parts=rf["path"].split("/")
        if len(parts)<2:
            messagebox.showinfo("Info","File is already at root."); return
        fname=parts[-1]
        parent_folder="/".join(parts[:-2]) if len(parts)>2 else ""
        dst=fname if not parent_folder else parent_folder+"/"+fname
        msg=f"Move {fname} up to {'root' if not parent_folder else parent_folder}"
        if not messagebox.askyesno("Move Out",
                                   f"Move  {rf['path']}\n→  {dst if dst else '/ root'}"): return
        self._log(f"Moving out  {rf['path']}  →  {dst}","y")
        def _w():
            try:
                self.app.engine.move_file(fn,rf["path"],dst,br,msg)
                self.app.root.after(0,lambda:(
                    self._log(f"Moved out  →  {dst}","g"),
                    self.do_load()))
            except Exception as ex:
                self.app.root.after(0,lambda:(
                    self._log(f"Error: {ex}","r"),
                    messagebox.showerror("Error",str(ex))))
        threading.Thread(target=_w,daemon=True).start()

    # ── RENAME ──
    def do_rename(self):
        rf=self._sel()
        if not rf: return
        fn=self._fn(); br=self._br()
        old=os.path.basename(rf["path"])
        new=simpledialog.askstring("Rename File",
                                  f"Current name:  {old}\n\nNew filename:",
                                  initialvalue=old,parent=self.app.root)
        if not new or new.strip()==old: return
        new=new.strip()
        folder=os.path.dirname(rf["path"])
        dst=new if not folder else folder+"/"+new
        msg=f"Rename {old} to {new}"
        self._log(f"Renaming  {old}  →  {new}","y")
        def _w():
            try:
                self.app.engine.move_file(fn,rf["path"],dst,br,msg)
                self.app.root.after(0,lambda:(
                    self._log(f"Renamed  →  {new}","g"),
                    self.do_load()))
            except Exception as ex:
                self.app.root.after(0,lambda:(
                    self._log(f"Error: {ex}","r"),
                    messagebox.showerror("Error",str(ex))))
        threading.Thread(target=_w,daemon=True).start()

    # ── DELETE ──
    def do_delete(self):
        rf=self._sel()
        if not rf: return
        fn=self._fn(); br=self._br()
        if not messagebox.askyesno("Delete File",
                                   f"Permanently delete:\n\n{rf['path']}\n\nThis cannot be undone."): return
        self._log(f"Deleting  {rf['path']}","r")
        def _w():
            try:
                self.app.engine.delete_file(fn,rf["path"],rf["sha"],br,
                                           f"Delete {rf['path']}")
                self.app.root.after(0,lambda:(
                    self._log(f"Deleted  {rf['path']}","g"),
                    self.do_load()))
            except Exception as ex:
                self.app.root.after(0,lambda:(
                    self._log(f"Error: {ex}","r"),
                    messagebox.showerror("Error",str(ex))))
        threading.Thread(target=_w,daemon=True).start()

    # ── NEW FILE ──
    def do_new_file(self):
        fn=self._fn()
        if not fn or not self.app.engine:
            messagebox.showwarning("Warning","Connect and select a repository first."); return
        folder=self._cur_folder
        suggestion=f"{folder}/" if folder else ""
        path=simpledialog.askstring("New File",
                                   f"File path (inside: {folder or 'root'}):",
                                   initialvalue=suggestion+"filename.txt",
                                   parent=self.app.root)
        if not path: return
        self._open_editor(fn,path.strip(),"",None,self._br())

    # ── NEW FOLDER ──
    def do_new_folder(self):
        fn=self._fn()
        if not fn or not self.app.engine:
            messagebox.showwarning("Warning","Connect and select a repository first."); return
        cur=self._cur_folder
        folder=simpledialog.askstring("New Folder",
                                     f"Folder path (inside: {cur or 'root'}):",
                                     initialvalue=f"{cur}/" if cur else "",
                                     parent=self.app.root)
        if not folder: return
        folder=folder.strip()
        self._log(f"Creating folder  {folder}","b")
        def _w():
            try:
                self.app.engine.create_folder(fn,folder,self._br(),
                                             f"Create folder {folder}")
                self.app.root.after(0,lambda:(
                    self._log(f"Folder created  {folder}","g"),
                    self.do_load()))
            except Exception as ex:
                self.app.root.after(0,lambda:(
                    self._log(f"Error: {ex}","r"),
                    messagebox.showerror("Error",str(ex))))
        threading.Thread(target=_w,daemon=True).start()

    # ── UPLOAD HERE ──
    def do_upload_here(self):
        fn=self._fn()
        if not fn or not self.app.engine:
            messagebox.showwarning("Warning","Connect and select a repository first."); return
        paths=filedialog.askopenfilenames(title="Select files to upload here")
        if not paths: return
        target=self._cur_folder
        items=self.app.engine.scan(list(paths))
        # flatten to just filename (upload into current folder)
        for it in items:
            it["rel_path"]=os.path.basename(it["rel_path"])
        if not items: return
        self._log(f"Uploading {len(items)} file(s) into  /{target or 'root'}  ...","b")
        commit=f"Upload files to {'root' if not target else target}"
        def _w():
            def cb(ev,data):
                if ev=="progress":
                    self.app.root.after(0,lambda:
                        self._log(f"  Uploaded  {data['file']}  ({data['uploaded']}/{data['total']})","g"))
                elif ev=="done":
                    self.app.root.after(0,lambda:(
                        self._log(f"Done — {data['uploaded']}/{data['total']} uploaded","g"),
                        self.do_load()))
                elif ev=="file_error":
                    self.app.root.after(0,lambda:
                        self._log(f"  Error  {data['file']}: {data['error']}","r"))
            self.app.engine.upload(fn,items,self._br(),commit,target,cb)
        threading.Thread(target=_w,daemon=True).start()


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════
class App:
    def __init__(self):
        self.engine=None; self.repos=[]; self.scanned=[]
        self.is_uploading=False; self.config=self._load_cfg()

        self.root=TkinterDnD.Tk() if DND else tk.Tk()
        self.root.title("GitHub Uploader Pro  —  v5.0")
        self.root.geometry("1280x800")
        self.root.minsize(1050,680)
        self.root.configure(bg=P["bg"])

        self._styles()
        self._build()
        self._load_token()
        self.root.mainloop()

    def _load_cfg(self):
        try:
            with open(CFG) as f: return json.load(f)
        except: return {}
    def _save_cfg(self):
        try:
            with open(CFG,"w") as f: json.dump(self.config,f)
        except: pass
    def _load_token(self):
        t=self.config.get("token","")
        if t: self.ent_token.insert(0,t)

    def _styles(self):
        s=ttk.Style(); s.theme_use("clam")
        for w in ("TCombobox","TEntry"):
            s.configure(w,fieldbackground=P["input"],background=P["border"],
                        foreground=P["text"],insertcolor=P["text"],
                        arrowcolor=P["teal"],selectbackground=P["navy2"],
                        selectforeground=P["text"],darkcolor=P["input"],
                        lightcolor=P["input"],bordercolor=P["border"],relief="flat")
            s.map(w,fieldbackground=[("readonly",P["input"])],
                  foreground=[("readonly",P["text"])])
        for sb in ("Vertical.TScrollbar","Horizontal.TScrollbar"):
            s.configure(sb,background=P["border"],troughcolor=P["bg2"],
                        arrowcolor=P["sub"])
        s.configure("TNotebook",background=P["bg"],borderwidth=0)
        s.configure("TNotebook.Tab",background=P["card"],foreground=P["sub"],
                    font=("Segoe UI",10),padding=[18,8])
        s.map("TNotebook.Tab",
              background=[("selected",P["navy2"]),("active",P["card2"])],
              foreground=[("selected",P["text"]),("active",P["teal"])])

    # ── helpers ──
    def _btn(self,p,t,bg,cmd,**kw):
        return tk.Button(p,text=t,bg=bg,fg="#fff",font=("Segoe UI",9,"bold"),
                        relief="flat",cursor="hand2",activebackground=bg,
                        activeforeground="#fff",command=cmd,**kw)
    def _stat(self,p,label,val,color):
        f=tk.Frame(p,bg=P["card2"],padx=14,pady=8)
        f.pack(side="left",fill="x",expand=True,padx=4)
        v=tk.Label(f,text=val,font=("Segoe UI",15,"bold"),bg=P["card2"],fg=color)
        v.pack()
        tk.Label(f,text=label,font=("Segoe UI",8),bg=P["card2"],fg=P["muted"]).pack()
        return v
    def _log(self,msg,tag="m"):
        ts=datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end",f"[{ts}]  ","m")
        self.log_box.insert("end",f"{msg}\n",tag)
        self.log_box.see("end")
    def _get_repo(self):
        d=self.repo_var.get()
        if not d: return None
        for pfx in ["Lock ","Globe "]:
            if d.startswith(pfx): d=d[len(pfx):]
        return d.strip().split()[-1] if d.strip() else None
    def _get_branch(self): return self.branch_cb.get().strip() or "main"
    def _validate_upload(self):
        ok=(self.engine and self.scanned and self.repo_var.get()
            and not self.is_uploading)
        if ok:
            self.btn_up.config(state="normal",bg=P["navy"],cursor="hand2")
        else:
            self.btn_up.config(state="disabled",bg=P["border"],cursor="arrow")
    def _toggle_pw(self,e=None):
        self._spw=not getattr(self,"_spw",False)
        self.ent_token.config(show="" if self._spw else "•")

    # ══════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════
    def _build(self):
        GradBar(self.root,P["teal"],P["navy"],h=4,bg=P["bg"]).pack(fill="x")
        main=tk.Frame(self.root,bg=P["bg"]); main.pack(fill="both",expand=True)

        # sidebar
        sb=tk.Frame(main,bg=P["sidebar"],width=288)
        sb.pack(side="left",fill="y"); sb.pack_propagate(False)
        self._build_sidebar(sb)

        tk.Frame(main,bg=P["border"],width=1).pack(side="left",fill="y")

        right=tk.Frame(main,bg=P["bg"])
        right.pack(side="left",fill="both",expand=True)
        self._build_right(right)

    # ── SIDEBAR ──────────────────────────────────────
    def _build_sidebar(self,sb):
        # Logo
        lf=tk.Frame(sb,bg=P["sidebar"]); lf.pack(fill="x",pady=(18,6))
        lc=tk.Canvas(lf,width=46,height=46,bg=P["sidebar"],highlightthickness=0)
        lc.pack(side="left",padx=(14,10))
        rounded_rect(lc,2,2,44,44,r=12,fill=P["navy2"],outline=P["teal"],width=2)
        lc.create_text(23,23,text="UP",fill=P["teal"],font=("Segoe UI",11,"bold"))
        tf=tk.Frame(lf,bg=P["sidebar"]); tf.pack(side="left")
        tk.Label(tf,text="GitHub Uploader",font=("Segoe UI",12,"bold"),
                bg=P["sidebar"],fg=P["text"]).pack(anchor="w")
        tk.Label(tf,text="Pro Edition v5.0",font=("Segoe UI",8),
                bg=P["sidebar"],fg=P["sub"]).pack(anchor="w")

        # version badge
        badge_c=tk.Canvas(sb,width=100,height=22,bg=P["sidebar"],highlightthickness=0)
        badge_c.pack(pady=(0,6))
        rounded_rect(badge_c,0,0,100,22,r=11,fill=P["purple2"],outline="")
        badge_c.create_text(50,11,text="ULTRA  v5.0",fill="#fff",
                           font=("Segoe UI",8,"bold"))

        GradBar(sb,P["teal"],P["purple"],h=2,bg=P["sidebar"]).pack(fill="x",padx=12,pady=(0,10))

        def section(t):
            f=tk.Frame(sb,bg=P["sidebar"]); f.pack(fill="x",padx=12,pady=(8,4))
            tk.Label(f,text=t,font=("Segoe UI",9,"bold"),
                    bg=P["sidebar"],fg=P["teal"]).pack(anchor="w")

        # ── AUTH ──
        section("Authentication")
        tw=tk.Frame(sb,bg=P["border"]); tw.pack(fill="x",padx=12,pady=(2,0))
        ti=tk.Frame(tw,bg=P["input"]); ti.pack(fill="x",padx=1,pady=1)
        tk.Label(ti,text="Token",bg=P["input"],fg=P["muted"],
                font=("Segoe UI",8)).pack(side="left",padx=(8,4))
        self.ent_token=tk.Entry(ti,show="•",font=("Consolas",10),
                               bg=P["input"],fg=P["text"],
                               insertbackground=P["text"],relief="flat",bd=5)
        self.ent_token.pack(side="left",fill="x",expand=True)
        eye=tk.Label(ti,text="Show",bg=P["input"],fg=P["sub"],
                    font=("Segoe UI",7),cursor="hand2")
        eye.pack(side="right",padx=6)
        eye.bind("<Button-1>",self._toggle_pw)

        self.btn_conn=tk.Button(sb,text="Connect to GitHub",
                               bg=P["navy"],fg="#fff",
                               font=("Segoe UI",10,"bold"),relief="flat",
                               pady=9,cursor="hand2",
                               activebackground=P["navy2"],
                               command=self.do_connect)
        self.btn_conn.pack(fill="x",padx=12,pady=(8,2))

        self.lbl_status=tk.Label(sb,text="Not connected",
                                font=("Segoe UI",8),
                                bg=P["sidebar"],fg=P["muted"])
        self.lbl_status.pack(pady=(0,2))

        link=tk.Label(sb,text="Create token on GitHub",
                     font=("Segoe UI",8,"underline"),
                     bg=P["sidebar"],fg=P["teal"],cursor="hand2")
        link.pack()
        link.bind("<Button-1>",lambda e:webbrowser.open(
            "https://github.com/settings/tokens/new?scopes=repo,delete_repo"))

        GradBar(sb,P["navy"],P["purple"],h=1,bg=P["sidebar"]).pack(fill="x",padx=12,pady=10)

        # ── REPO ──
        section("Repository")
        self.repo_var=tk.StringVar()
        self.repo_cb=ttk.Combobox(sb,textvariable=self.repo_var,
                                  state="readonly",font=("Segoe UI",9))
        self.repo_cb.pack(fill="x",padx=12,pady=(3,3))
        self.repo_cb.bind("<<ComboboxSelected>>",self._on_repo_sel)

        rr=tk.Frame(sb,bg=P["sidebar"]); rr.pack(fill="x",padx=12,pady=(2,4))
        self._btn(rr,"Refresh",P["border"],self.do_refresh_repos,
                 padx=8,pady=4).pack(side="left",padx=(0,4))
        self._btn(rr,"New Repo",P["navy2"],self.do_create_repo,
                 padx=8,pady=4).pack(side="left")

        self.lbl_repo=tk.Label(sb,text="",font=("Segoe UI",8),
                              bg=P["sidebar"],fg=P["sub"],
                              wraplength=250,justify="left")
        self.lbl_repo.pack(anchor="w",padx=12,pady=(0,2))

        # new repo input
        nw=tk.Frame(sb,bg=P["border"]); nw.pack(fill="x",padx=12,pady=(0,2))
        ni=tk.Frame(nw,bg=P["input"]); ni.pack(fill="x",padx=1,pady=1)
        self.ent_newrepo=tk.Entry(ni,font=("Segoe UI",9),bg=P["input"],
                                  fg=P["sub"],insertbackground=P["text"],
                                  relief="flat",bd=5)
        self.ent_newrepo.pack(side="left",fill="x",expand=True)
        self.ent_newrepo.insert(0,"new-repo-name")
        self.ent_newrepo.bind("<FocusIn>",
            lambda e:self.ent_newrepo.delete(0,"end")
            if self.ent_newrepo.get()=="new-repo-name" else None)
        self.priv=tk.BooleanVar(value=False)
        tk.Checkbutton(ni,text="Priv",variable=self.priv,
                      bg=P["input"],fg=P["sub"],selectcolor=P["border"],
                      activebackground=P["input"],font=("Segoe UI",8)
                      ).pack(side="right",padx=4)

        GradBar(sb,P["purple"],P["teal"],h=1,bg=P["sidebar"]).pack(fill="x",padx=12,pady=8)

        # ── BRANCH / COMMIT ──
        section("Branch & Commit")
        br=tk.Frame(sb,bg=P["sidebar"]); br.pack(fill="x",padx=12,pady=(3,3))
        self.branch_cb=ttk.Combobox(br,font=("Segoe UI",9),width=12)
        self.branch_cb.pack(side="left",fill="x",expand=True,padx=(0,4))
        self.branch_cb.set("main")
        self._btn(br,"+ Branch",P["border"],self.do_create_branch,
                 padx=6,pady=4).pack(side="right")

        tw2=tk.Frame(sb,bg=P["border"]); tw2.pack(fill="x",padx=12,pady=(2,3))
        ti2=tk.Frame(tw2,bg=P["input"]); ti2.pack(fill="x",padx=1,pady=1)
        tk.Label(ti2,text="Target Folder",bg=P["input"],fg=P["muted"],
                font=("Segoe UI",7)).pack(side="left",padx=(6,2))
        self.ent_target=tk.Entry(ti2,font=("Segoe UI",9),bg=P["input"],
                                 fg=P["sub"],insertbackground=P["text"],
                                 relief="flat",bd=4)
        self.ent_target.pack(fill="x",expand=True)
        self.ent_target.insert(0,"optional/folder")
        self.ent_target.bind("<FocusIn>",
            lambda e:self.ent_target.delete(0,"end")
            if "optional" in self.ent_target.get() else None)

        tw3=tk.Frame(sb,bg=P["border"]); tw3.pack(fill="x",padx=12,pady=(2,3))
        ti3=tk.Frame(tw3,bg=P["input"]); ti3.pack(fill="x",padx=1,pady=1)
        tk.Label(ti3,text="Commit Msg",bg=P["input"],fg=P["muted"],
                font=("Segoe UI",7)).pack(side="left",padx=(6,2))
        self.ent_commit=tk.Entry(ti3,font=("Segoe UI",9),bg=P["input"],
                                 fg=P["text"],insertbackground=P["text"],
                                 relief="flat",bd=4)
        self.ent_commit.pack(fill="x",expand=True)
        self.ent_commit.insert(0,"Upload via GitHub Uploader Pro")

        tk.Frame(sb,bg=P["sidebar"]).pack(fill="y",expand=True)
        GradBar(sb,P["teal"],P["navy"],h=1,bg=P["sidebar"]).pack(fill="x",padx=12,pady=(0,6))
        tk.Label(sb,text="github.com  •  Uploader Pro v5.0",
                font=("Segoe UI",7),bg=P["sidebar"],fg=P["muted"]).pack(pady=(0,8))

    # ── RIGHT PANEL ──────────────────────────────────
    def _build_right(self,parent):
        top=tk.Frame(parent,bg=P["card"],height=52); top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top,text="GitHub Uploader Pro",
                font=("Segoe UI",14,"bold"),
                bg=P["card"],fg=P["text"]).pack(side="left",padx=20,pady=12)

        self.btn_up=tk.Button(top,text="Upload to GitHub",
                             bg=P["border"],fg=P["muted"],
                             font=("Segoe UI",11,"bold"),relief="flat",
                             padx=22,pady=7,cursor="arrow",state="disabled",
                             command=self.do_upload)
        self.btn_up.pack(side="right",padx=14,pady=8)

        GradBar(parent,P["teal"],P["navy"],h=2,bg=P["bg"]).pack(fill="x")

        self.nb=ttk.Notebook(parent)
        self.nb.pack(fill="both",expand=True)

        t1=tk.Frame(self.nb,bg=P["bg"])
        self.nb.add(t1,text="  Drop Zone  ")
        self._build_drop(t1)

        t2=tk.Frame(self.nb,bg=P["bg"])
        self.nb.add(t2,text="  Remote Files  ")
        self.remote_panel=RemoteTreePanel(t2,self)
        self.remote_panel.pack(fill="both",expand=True)

        t3=tk.Frame(self.nb,bg=P["bg"])
        self.nb.add(t3,text="  Progress & Log  ")
        self._build_progress(t3)

    # ── TAB 1: DROP ──────────────────────────────────
    def _build_drop(self,parent):
        pw=tk.PanedWindow(parent,orient="horizontal",bg=P["bg"],sashwidth=5)
        pw.pack(fill="both",expand=True,padx=10,pady=10)

        # left
        left=tk.Frame(pw,bg=P["bg"]); pw.add(left,width=420,minsize=300)

        self.drop_out=tk.Frame(left,bg=P["bhi"],bd=2)
        self.drop_out.pack(fill="both",expand=True,pady=(0,8))
        self.drop_box=tk.Frame(self.drop_out,bg=P["card"],cursor="hand2")
        self.drop_box.pack(fill="both",expand=True,padx=2,pady=2)

        dz=tk.Frame(self.drop_box,bg=P["card"])
        dz.place(relx=0.5,rely=0.45,anchor="center")

        # big canvas icon
        ic=tk.Canvas(dz,width=90,height=90,bg=P["card"],highlightthickness=0)
        ic.pack()
        rounded_rect(ic,5,5,85,85,r=20,fill=P["navy2"],outline=P["teal"],width=2)
        ic.create_text(45,45,text="DROP",fill=P["teal"],font=("Segoe UI",14,"bold"))

        self.lbl_dz_title=tk.Label(dz,text="Drop Anything Here",
                                  font=("Segoe UI",16,"bold"),
                                  bg=P["card"],fg=P["text"])
        self.lbl_dz_title.pack(pady=(12,4))
        self.lbl_dz_sub=tk.Label(dz,
            text="Files  •  Folders  •  ZIP  •  Images  •  Videos  •  Audio  •  Code",
            font=("Segoe UI",10),bg=P["card"],fg=P["sub"],justify="center")
        self.lbl_dz_sub.pack()

        GradBar(dz,P["teal"],P["purple"],h=2,bg=P["card"]).pack(fill="x",pady=10)

        br=tk.Frame(dz,bg=P["card"]); br.pack()
        self._btn(br,"Folder",P["navy2"],self.browse_folder,
                 padx=14,pady=8).pack(side="left",padx=3)
        self._btn(br,"Files",P["navy"],self.browse_files,
                 padx=14,pady=8).pack(side="left",padx=3)
        self._btn(br,"ZIP",P["purple2"],self.browse_zip,
                 padx=14,pady=8).pack(side="left",padx=3)

        if not DND:
            tk.Label(dz,text="Install tkinterdnd2 for drag & drop support",
                    font=("Segoe UI",8),bg=P["card"],fg=P["amber"]).pack(pady=(8,0))

        if DND:
            self.drop_box.drop_target_register(DND_FILES)
            self.drop_box.dnd_bind('<<DropEnter>>',self._dnd_in)
            self.drop_box.dnd_bind('<<DropLeave>>',self._dnd_out)
            self.drop_box.dnd_bind('<<Drop>>',self._dnd_drop)

        for w in [self.drop_box,dz,self.lbl_dz_title,self.lbl_dz_sub,ic]:
            w.bind("<Button-1>",lambda e:self.browse_folder())

        # stats
        sf=tk.Frame(left,bg=P["card2"]); sf.pack(fill="x")
        self.s_files=self._stat(sf,"Files","0",P["teal"])
        self.s_size =self._stat(sf,"Total Size","—",P["cyan"])
        self.s_types=self._stat(sf,"File Types","—",P["purple"])

        # right: queue
        right=tk.Frame(pw,bg=P["bg"]); pw.add(right,minsize=260)
        qh=tk.Frame(right,bg=P["card2"]); qh.pack(fill="x",pady=(0,3))
        tk.Label(qh,text="Upload Queue",font=("Segoe UI",10,"bold"),
                bg=P["card2"],fg=P["teal"]).pack(side="left",padx=12,pady=8)
        self._btn(qh,"Clear All",P["border"],self.clear_queue,
                 padx=8,pady=4).pack(side="right",padx=8,pady=6)

        qt=tk.Frame(right,bg=P["bg"]); qt.pack(fill="both",expand=True)
        self.q_tree=ttk.Treeview(qt,
                                  columns=("type","path","size"),
                                  show="headings",height=20,
                                  selectmode="extended")
        self.q_tree.heading("type",text="Type")
        self.q_tree.heading("path",text="Path")
        self.q_tree.heading("size",text="Size")
        self.q_tree.column("type",width=55,anchor="center")
        self.q_tree.column("path",width=290)
        self.q_tree.column("size",width=80,anchor="e")

        qs=ttk.Scrollbar(qt,orient="vertical",command=self.q_tree.yview)
        self.q_tree.configure(yscrollcommand=qs.set)
        qs.pack(side="right",fill="y"); self.q_tree.pack(fill="both",expand=True)

        qm=tk.Menu(self.root,tearoff=0,bg=P["card"],fg=P["text"],
                  activebackground=P["navy2"],font=("Segoe UI",9))
        qm.add_command(label="Remove Selected",command=self.remove_from_queue)
        self.q_tree.bind("<Button-3>",lambda e:(
            self.q_tree.identify_row(e.y) and
            self.q_tree.selection_set(self.q_tree.identify_row(e.y)),
            qm.tk_popup(e.x_root,e.y_root)))

    # ── TAB 3: PROGRESS ──────────────────────────────
    def _build_progress(self,parent):
        sb=tk.Frame(parent,bg=P["card2"]); sb.pack(fill="x",padx=10,pady=(8,6))
        self.p_up=self._stat(sb,"Uploaded","0",P["green"])
        self.p_tot=self._stat(sb,"Total","0",P["teal"])
        self.p_sz=self._stat(sb,"Data","—",P["purple"])
        self.p_spd=self._stat(sb,"Speed","—",P["amber"])
        self.p_t=self._stat(sb,"Time","—",P["cyan"])

        pb=tk.Frame(parent,bg=P["border"],height=14)
        pb.pack(fill="x",padx=10,pady=(0,4)); pb.pack_propagate(False)
        self.pbc=tk.Canvas(pb,height=14,bg=P["input"],highlightthickness=0)
        self.pbc.pack(fill="both",expand=True,padx=1,pady=1)
        self.pb_r=self.pbc.create_rectangle(0,0,0,14,fill=P["navy"],outline="")
        self.pb_g=self.pbc.create_rectangle(0,0,0,14,fill=P["teal"],
                                            outline="",stipple="gray50")

        self.lbl_pct=tk.Label(parent,text="0 %",font=("Segoe UI",13,"bold"),
                             bg=P["bg"],fg=P["text"])
        self.lbl_pct.pack()
        self.lbl_cf=tk.Label(parent,text="Ready",font=("Consolas",9),
                            bg=P["bg"],fg=P["muted"],wraplength=950)
        self.lbl_cf.pack(pady=(0,8))

        GradBar(parent,P["navy"],P["teal"],h=1,bg=P["bg"]).pack(fill="x",padx=10,pady=(0,8))

        tk.Label(parent,text="Activity Log",font=("Segoe UI",9,"bold"),
                bg=P["bg"],fg=P["teal"]).pack(anchor="w",padx=12)

        lf=tk.Frame(parent,bg=P["bg"]); lf.pack(fill="both",expand=True,padx=10,pady=(3,8))
        self.log_box=tk.Text(lf,font=("Consolas",9),bg=P["input"],fg=P["text"],
                            insertbackground=P["text"],relief="flat",bd=8,wrap="word",
                            selectbackground=P["navy2"])
        ls=ttk.Scrollbar(lf,orient="vertical",command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=ls.set)
        ls.pack(side="right",fill="y"); self.log_box.pack(fill="both",expand=True)

        for tag,col in [("g",P["green"]),("b",P["teal"]),("r",P["red"]),
                        ("o",P["amber"]),("m",P["muted"]),("c",P["cyan"]),
                        ("p",P["purple"]),("y",P["amber"]),("H",P["text"])]:
            self.log_box.tag_config(tag,foreground=col)
        self.log_box.tag_config("H",font=("Consolas",9,"bold"))

        self._log("GitHub Uploader Pro v5.0 ready","b")
        self._log("Tree Browser  •  Move  •  Rename  •  Upload  •  Full CRUD","m")
        if not DND: self._log("Tip: pip install tkinterdnd2  for drag & drop","o")

    # ══════════════════════════════════════════════════
    #  QUEUE
    # ══════════════════════════════════════════════════
    def _add(self,paths):
        if self.engine: items=self.engine.scan(paths)
        else:
            items=[]
            for p in paths:
                p=p.strip().strip("{}\"'")
                if os.path.isdir(p):
                    for root,dirs,files in os.walk(p):
                        dirs[:]=[d for d in dirs if d not in SKIP]
                        for f in files:
                            fp=os.path.join(root,f)
                            rel=os.path.relpath(fp,os.path.dirname(p)).replace("\\","/")
                            items.append({"full_path":fp,"rel_path":rel,
                                         "size":os.path.getsize(fp),"ext":fext(fp)})
                elif os.path.isfile(p):
                    fname=os.path.basename(p)
                    items.append({"full_path":p,"rel_path":fname,
                                 "size":os.path.getsize(p),"ext":fext(p)})

        self.scanned.extend(items)
        for f in items:
            badge=flabel(f["rel_path"]); col=fcolor(f["rel_path"])
            self.q_tree.insert("","end",
                values=(badge,f["rel_path"],fmt_size(f["size"])),
                tags=(badge,))
            self.q_tree.tag_configure(badge,foreground=col)
        self._refresh_stats(); self._validate_upload(); self.nb.select(0)

    def _refresh_stats(self):
        n=len(self.scanned)
        sz=sum(f["size"] for f in self.scanned)
        tp=len({f["ext"] for f in self.scanned})
        self.s_files.config(text=str(n))
        self.s_size.config(text=fmt_size(sz))
        self.s_types.config(text=str(tp))
        if n>0:
            self.drop_out.config(bg=P["green2"])
            self.lbl_dz_title.config(text=f"{n} item(s) queued")
            self.lbl_dz_sub.config(text=f"{fmt_size(sz)}  •  {tp} types  •  Ready")
        else:
            self.drop_out.config(bg=P["bhi"])
            self.lbl_dz_title.config(text="Drop Anything Here")
            self.lbl_dz_sub.config(
                text="Files  •  Folders  •  ZIP  •  Images  •  Videos  •  Audio  •  Code")

    def clear_queue(self):
        self.scanned=[]
        for i in self.q_tree.get_children(): self.q_tree.delete(i)
        self._refresh_stats(); self._validate_upload()

    def remove_from_queue(self):
        for sel in self.q_tree.selection():
            vals=self.q_tree.item(sel,"values")
            rel=vals[1] if len(vals)>1 else ""
            self.scanned=[f for f in self.scanned if f["rel_path"]!=rel]
            self.q_tree.delete(sel)
        self._refresh_stats(); self._validate_upload()

    # ── BROWSE ──
    def browse_folder(self):
        p=filedialog.askdirectory(title="Select Folder")
        if p: self._add([p])
    def browse_files(self):
        ps=filedialog.askopenfilenames(title="Select Files",
                                      filetypes=[("All Files","*.*")])
        if ps: self._add(list(ps))
    def browse_zip(self):
        p=filedialog.askopenfilename(title="Select ZIP",
                                    filetypes=[("ZIP","*.zip"),("All","*.*")])
        if p: self._add([p])

    def _dnd_in(self,e):
        self.drop_out.config(bg=P["navy"])
        self.lbl_dz_title.config(text="Drop it now",fg=P["teal"])
    def _dnd_out(self,e):
        self._refresh_stats(); self.lbl_dz_title.config(fg=P["text"])
    def _dnd_drop(self,e):
        raw=e.data.strip()
        paths=re.findall(r'\{([^}]+)\}|(\S+)',raw)
        paths=[a or b for a,b in paths]
        self._add(paths)

    # ── GITHUB ──
    def do_connect(self):
        token=self.ent_token.get().strip()
        if not token: messagebox.showwarning("Warning","Enter your GitHub token."); return
        self.btn_conn.config(text="Connecting ...",state="disabled")
        self.lbl_status.config(text="Connecting ...",fg=P["amber"])
        def _w():
            try:
                eng=Engine(token); user=eng.username
                self.root.after(0,lambda:self._on_conn(eng,token,user))
            except Exception as ex:
                self.root.after(0,lambda:self._conn_fail(str(ex)))
        threading.Thread(target=_w,daemon=True).start()

    def _on_conn(self,eng,token,user):
        self.engine=eng; self.config["token"]=token; self._save_cfg()
        self.btn_conn.config(text="Connected",state="normal",bg=P["green2"])
        self.lbl_status.config(text=f"Connected as  @{user}",fg=P["green"])
        self._log(f"Connected as @{user}","g")
        self.do_refresh_repos(); self._validate_upload()

    def _conn_fail(self,err):
        self.btn_conn.config(text="Connect to GitHub",state="normal",bg=P["navy"])
        self.lbl_status.config(text="Connection failed",fg=P["red"])
        self._log(f"Auth error: {err}","r"); messagebox.showerror("Auth Failed",err)

    def do_refresh_repos(self):
        if not self.engine: return
        def _w():
            try:
                repos=self.engine.list_repos()
                self.root.after(0,lambda:self._on_repos(repos))
            except Exception as ex:
                self.root.after(0,lambda:self._log(f"Error: {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    def _on_repos(self,repos):
        self.repos=repos
        disp=[(f"Lock {r['full_name']}" if r["private"] else f"Globe {r['full_name']}")
              for r in repos]
        self.repo_cb["values"]=disp
        if disp: self.repo_cb.current(0); self._on_repo_sel()
        self._log(f"Loaded {len(repos)} repositories","g"); self._validate_upload()

    def _on_repo_sel(self,e=None):
        fn=self._get_repo()
        if not fn: return
        for r in self.repos:
            if r["full_name"]==fn:
                self.lbl_repo.config(
                    text=f"{'Private' if r['private'] else 'Public'}  •  "
                         f"{r['description'][:50] or 'No description'}")
                self.branch_cb.set(r["default_branch"]); break
        def _w():
            try:
                brs=self.engine.list_branches(fn)
                self.root.after(0,lambda:self.branch_cb.config(values=brs))
            except: pass
        threading.Thread(target=_w,daemon=True).start()
        self._validate_upload()

    def do_create_repo(self):
        if not self.engine: messagebox.showwarning("Warning","Connect first."); return
        name=self.ent_newrepo.get().strip()
        if not name or name=="new-repo-name":
            messagebox.showwarning("Warning","Enter a repository name."); return
        def _w():
            try:
                repo=self.engine.create_repo(name,private=self.priv.get())
                self.root.after(0,lambda:(self._log(f"Created: {repo.full_name}","g"),
                                         self.do_refresh_repos()))
            except Exception as ex:
                self.root.after(0,lambda:self._log(f"Error: {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    def do_create_branch(self):
        if not self.engine: return
        fn=self._get_repo()
        if not fn: messagebox.showwarning("Warning","Select a repository."); return
        name=simpledialog.askstring("New Branch","Branch name:",parent=self.root)
        if not name: return
        src=self._get_branch()
        def _w():
            try:
                self.engine.create_branch(fn,name,src)
                brs=self.engine.list_branches(fn)
                self.root.after(0,lambda:(self.branch_cb.config(values=brs),
                                         self.branch_cb.set(name),
                                         self._log(f"Branch created: {name}","g")))
            except Exception as ex:
                self.root.after(0,lambda:self._log(f"Error: {ex}","r"))
        threading.Thread(target=_w,daemon=True).start()

    # ── UPLOAD ──
    def do_upload(self):
        if not self.engine or not self.scanned: return
        fn=self._get_repo()
        if not fn: return
        branch=self._get_branch()
        commit=self.ent_commit.get().strip() or "Upload files"
        target=self.ent_target.get().strip()
        if "optional" in target: target=""
        n=len(self.scanned)
        if not messagebox.askyesno("Upload",
                                   f"Upload {n} file(s)\n→ {fn}  [{branch}]"
                                   f"{f'  /  {target}' if target else ''}?"): return
        self.is_uploading=True
        self.btn_up.config(state="disabled",text="Uploading ...",bg=P["amber"])
        self.nb.select(2)
        self.p_up.config(text="0"); self.p_tot.config(text=str(n))
        self.p_sz.config(text="—"); self.p_spd.config(text="—")
        self.lbl_pct.config(text="0 %"); self.lbl_cf.config(text="Starting ...")
        self.pbc.coords(self.pb_r,0,0,0,14); self.pbc.coords(self.pb_g,0,0,0,14)
        self._log("="*55,"H"); self._log(f"Upload  →  {fn}  [{branch}]","H")
        fc=list(self.scanned)
        def _w():
            def cb(ev,data):
                self.root.after(0,lambda:self._uev(ev,data,fn))
            try: self.engine.upload(fn,fc,branch,commit,target,cb)
            except Exception as ex:
                self.root.after(0,lambda:self._uev("fatal",{"error":str(ex)},fn))
        threading.Thread(target=_w,daemon=True).start()

    def _uev(self,ev,data,repo):
        if ev=="start": self.p_tot.config(text=str(data["total"]))
        elif ev=="uploading":
            f=data["file"]; self.lbl_cf.config(text=f)
        elif ev=="progress":
            up=data["uploaded"]; tot=data["total"]
            b=data["bytes"]; spd=data.get("speed",0)
            pct=int(up/tot*100) if tot else 0
            self.p_up.config(text=str(up)); self.p_sz.config(text=fmt_size(b))
            self.p_spd.config(text=f"{fmt_size(int(spd))}/s")
            self.lbl_pct.config(text=f"{pct} %")
            w=self.pbc.winfo_width(); fw=int(w*pct/100)
            self.pbc.coords(self.pb_r,0,0,fw,14)
            self.pbc.coords(self.pb_g,max(0,fw-20),0,fw,14)
            f=data["file"]
            self._log(f"  Uploaded  {f}  ({up}/{tot})","g")
        elif ev=="file_error":
            self._log(f"  Error  {data['file']}: {data['error']}","r")
        elif ev=="done":
            up=data["uploaded"]; tot=data["total"]
            elapsed=data.get("elapsed",0)
            w=self.pbc.winfo_width()
            self.pbc.coords(self.pb_r,0,0,w,14)
            self.pbc.coords(self.pb_g,max(0,w-30),0,w,14)
            self.lbl_pct.config(text="100 %"); self.lbl_cf.config(text="Done !")
            self.p_t.config(text=fmt_time(elapsed))
            self.is_uploading=False
            self.btn_up.config(text="Upload to GitHub",bg=P["navy"])
            self._validate_upload()
            self._log(f"Done  —  {up}/{tot}  in  {fmt_time(elapsed)}","g")
            self._log("="*55,"H")
            if messagebox.askyesno("Done","Upload complete!\n\nOpen repository in browser?"):
                webbrowser.open(f"https://github.com/{repo}")
        elif ev=="fatal":
            self.is_uploading=False
            self.btn_up.config(text="Upload to GitHub",bg=P["navy"])
            self._validate_upload()
            self._log(f"Fatal error: {data['error']}","r")
            messagebox.showerror("Error",data["error"])


# ══════════════════════════════════════════════════════════════
if __name__=="__main__":
    print("""
  ╔══════════════════════════════════════════════════════╗
  ║  GitHub Uploader Pro  —  Ultra v5.0                 ║
  ║  Tree Browser · Move · Rename · Delete · Upload     ║
  ╚══════════════════════════════════════════════════════╝
""")
    App()