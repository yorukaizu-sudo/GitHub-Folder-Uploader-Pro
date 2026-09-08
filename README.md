# 🚀 GitHub Folder Uploader Pro

GitHub Folder Uploader Pro adalah aplikasi desktop sederhana untuk mengelola dan meng-upload project ke GitHub tanpa harus menggunakan perintah Git secara manual.

Cukup:

1. Masukkan GitHub Token
2. Pilih atau Drag & Drop folder
3. Pilih repository
4. Klik Upload
5. Selesai ✅

Aplikasi juga dapat digunakan untuk membuat repository, melihat file repository, membuat file baru, mengedit file, menghapus file, serta mengelola branch.

---

# ✨ Fitur

- 🚀 Upload folder ke GitHub
- 📂 Drag & Drop folder
- 🔄 Update file yang sudah ada
- ➕ Membuat repository baru
- 🌐 Support repository Public
- 🔒 Support repository Private
- 📝 Edit file GitHub langsung dari aplikasi
- 📄 Membuat file baru
- 🗑️ Menghapus file
- 🌿 Melihat branch
- 🌿 Membuat branch baru
- 🗂️ Remote File Manager
- 📊 Progress upload
- 💾 Informasi ukuran upload
- ⚡ Informasi kecepatan upload
- 📋 Activity Log
- 🔑 Menyimpan GitHub Token
- 🌙 Modern GitHub Dark UI
- 📦 Bisa dijadikan aplikasi `.exe`

---

# 🖥️ Persyaratan

Untuk menjalankan aplikasi ini dibutuhkan:

- Windows 10 / Windows 11
- Python 3.10 atau lebih baru
- Internet Connection
- Akun GitHub

Download Python:

https://www.python.org/downloads/

Saat meng-install Python, pastikan mencentang:

```text
☑ Add Python to PATH
```

Kemudian lanjutkan instalasi Python seperti biasa.

---

# 📁 Struktur Project

Contoh struktur folder:

```text
GitHubUploader/
│
├── github_uploader.py
├── README.md
└── icon.ico
```

File utama aplikasi adalah:

```text
github_uploader.py
```

---

# 📦 1. Install Dependency

Buka CMD di folder aplikasi.

Contoh:

```cmd
cd C:\Users\yoruk\Documents\TESTER
```

Kemudian cek Python:

```cmd
python --version
```

Contoh output:

```text
Python 3.12.4
```

Upgrade pip terlebih dahulu:

```cmd
python -m pip install --upgrade pip
```

Install PyGithub:

```cmd
pip install PyGithub
```

Untuk mengaktifkan fitur Drag & Drop:

```cmd
pip install tkinterdnd2
```

Atau install semuanya sekaligus:

```cmd
pip install PyGithub tkinterdnd2
```

---

# 🚀 2. Menjalankan Aplikasi

Masuk ke folder tempat `github_uploader.py` berada.

Contoh:

```cmd
cd C:\Users\yoruk\Documents\TESTER
```

Jalankan:

```cmd
python github_uploader.py
```

Jika berhasil, jendela:

```text
GitHub Folder Uploader Pro
```

akan muncul.

---

# 🔑 3. Membuat GitHub Personal Access Token

Aplikasi memerlukan GitHub Personal Access Token agar dapat mengakses repository.

Buka:

https://github.com/settings/tokens

Kemudian:

```text
Settings
↓
Developer settings
↓
Personal access tokens
↓
Tokens (classic)
↓
Generate new token
↓
Generate new token (classic)
```

Atau buka langsung:

https://github.com/settings/tokens/new

Isi:

```text
Note:
GitHub Uploader Pro

Expiration:
90 days
```

Atau pilih:

```text
No expiration
```

jika memang diperlukan.

Pada bagian permissions/scopes, centang:

```text
☑ repo
```

`repo` dibutuhkan untuk mengelola repository dan melakukan upload/update file.

Jika ingin menggunakan fitur menghapus repository, tambahkan:

```text
☑ delete_repo
```

PERHATIAN:

`delete_repo` hanya diperlukan jika aplikasi memang memiliki fitur untuk menghapus repository.

Setelah itu klik:

```text
Generate token
```

GitHub akan menghasilkan token seperti:

```text
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

COPY TOKEN tersebut.

⚠️ JANGAN memberikan token kepada orang lain.

⚠️ Jangan memasukkan token ke source code.

⚠️ Jangan upload token ke repository GitHub.

---

# 🔌 4. Connect GitHub

Buka aplikasi.

Pada:

```text
GitHub Access Token
```

paste token:

```text
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Kemudian klik:

```text
Connect
```

Jika berhasil akan muncul:

```text
🟢 Terhubung: @username
```

Contoh:

```text
🟢 Terhubung: @yorukaizu-sudo
```

Dan log:

```text
✅ Terhubung ke GitHub sebagai @yorukaizu-sudo
📦 3 repository ditemukan
```

---

# 📂 5. Memilih Folder Project

Misalnya project berada di:

```text
C:\Users\yoruk\Documents\MyProject
```

Ada dua cara memilih folder.

## Cara A - Browse Folder

Klik:

```text
📁 Browse Folder
```

Kemudian pilih:

```text
C:\Users\yoruk\Documents\MyProject
```

## Cara B - Drag & Drop

Drag folder:

```text
MyProject
```

dari Windows Explorer ke area:

```text
Drop Folder Disini
```

Aplikasi akan melakukan scanning.

Contoh:

```text
📂 MyProject
📄 21 files
💾 385 KB
```

---

# 🚫 Folder yang Otomatis Diabaikan

Untuk menghindari file yang tidak diperlukan, aplikasi akan mengabaikan beberapa folder.

Contoh:

```text
.git
node_modules
__pycache__
venv
.venv
env
dist
build
.idea
.vscode
```

Contohnya apabila project Node.js memiliki:

```text
MyProject/
│
├── node_modules/
├── src/
├── package.json
└── README.md
```

`node_modules` tidak akan di-upload.

---

# 📦 6. Upload ke Repository yang Sudah Ada

Setelah GitHub terhubung, pilih repository dari dropdown.

Contoh:

```text
yorukaizu-sudo/saweria-api-new
```

Pilih branch:

```text
main
```

Isi Commit Message:

```text
Update project
```

Kemudian klik:

```text
🚀 UPLOAD FOLDER TO GITHUB
```

Konfirmasi:

```text
Upload 21 file ke:

yorukaizu-sudo/saweria-api-new

Branch:
main
```

Klik:

```text
Yes
```

Upload akan berjalan.

---

# 🔄 7. Update Project yang Sudah Ada

Anda tidak perlu membuat repository baru setiap kali ada perubahan.

Misalnya sebelumnya sudah meng-upload:

```text
index.py
config.json
README.md
```

Kemudian `index.py` di komputer diedit.

Pilih folder project yang sama.

Pilih repository yang sama:

```text
yorukaizu-sudo/saweria-api-new
```

Gunakan commit:

```text
Update aplikasi
```

Klik:

```text
UPLOAD FOLDER TO GITHUB
```

Jika file sudah tersedia di GitHub, aplikasi akan melakukan:

```text
UPDATE
```

Jika file belum tersedia, aplikasi akan melakukan:

```text
CREATE
```

Jadi:

```text
File lama    → Update
File baru    → Create
```

---

# ➕ 8. Membuat Repository Baru

Anda juga dapat membuat repository langsung dari aplikasi.

Masukkan nama:

```text
my-new-project
```

Pilih:

```text
Public
```

atau:

```text
🔒 Private
```

Kemudian klik:

```text
➕ Create
```

Jika berhasil:

```text
✅ Repository dibuat:
yorukaizu-sudo/my-new-project
```

Klik Refresh jika repository belum muncul:

```text
🔄
```

Kemudian pilih repository baru tersebut.

---

# 🌿 9. Memilih Branch

Secara default aplikasi menggunakan:

```text
main
```

Jika repository memiliki:

```text
main
develop
testing
production
```

Anda dapat memilih branch dari dropdown.

Contoh:

```text
develop
```

Upload selanjutnya akan masuk ke:

```text
develop
```

bukan ke:

```text
main
```

---

# 🌿 10. Membuat Branch Baru

Pilih repository.

Kemudian pilih source branch:

```text
main
```

Klik:

```text
🌿 New Branch
```

Masukkan:

```text
development
```

Aplikasi akan membuat:

```text
main
└── development
```

Setelah itu branch dapat digunakan untuk upload.

---

# 🗂️ 11. Melihat File Repository

Pilih repository terlebih dahulu.

Klik:

```text
🔄 Load Files
```

Aplikasi akan menampilkan file yang tersedia di repository.

Contoh:

```text
README.md
package.json
src/index.js
src/config.js
public/index.html
```

---

# 📝 12. Edit File GitHub Langsung

Klik:

```text
🔄 Load Files
```

Pilih file.

Contoh:

```text
README.md
```

Kemudian klik:

```text
📝 Edit Selected
```

Editor akan terbuka.

Edit isi file.

Contoh:

```markdown
# My Project

Project terbaru saya.
```

Masukkan commit:

```text
Update README
```

Klik:

```text
💾 Save & Push
```

Perubahan langsung dikirim ke GitHub.

---

# 📄 13. Membuat File Baru

Klik:

```text
📄 Create New File
```

Masukkan path.

Contoh:

```text
src/config.py
```

Editor akan terbuka.

Contoh isi:

```python
APP_NAME = "My Application"
VERSION = "1.0.0"

DEBUG = True
```

Commit:

```text
Create config.py
```

Klik:

```text
Create & Push
```

File akan dibuat di:

```text
src/config.py
```

---

# 🗑️ 14. Menghapus File

Klik:

```text
🔄 Load Files
```

Pilih file yang akan dihapus.

Contoh:

```text
old_file.py
```

Klik:

```text
🗑️ Delete Selected
```

Aplikasi akan meminta konfirmasi.

Klik:

```text
Yes
```

File kemudian dihapus melalui commit GitHub.

---

# 📊 15. Progress Upload

Saat proses upload berlangsung aplikasi akan menampilkan:

```text
Uploaded
21

Total
30

Data
542 KB

Speed
120 KB/s

Progress
70%
```

Log akan terlihat seperti:

```text
🚀 Upload dimulai
✅ index.py
✅ config.py
✅ README.md
✅ src/app.py
✅ src/database.py
```

Jika selesai:

```text
🎉 Selesai!

30/30 file berhasil di-upload.
```

---

# ⚠️ Troubleshooting

## Error: PyGithub tidak ditemukan

Error:

```text
ModuleNotFoundError: No module named 'github'
```

Jalankan:

```cmd
python -m pip install PyGithub
```

---

## Error tkinterdnd2

Error:

```text
ModuleNotFoundError: No module named 'tkinterdnd2'
```

Install:

```cmd
python -m pip install tkinterdnd2
```

Fitur Drag & Drop membutuhkan package tersebut.

---

# ❌ Error GitHub 401

Contoh:

```text
401 Bad credentials
```

Artinya token tidak valid atau sudah expired.

Buat token baru:

https://github.com/settings/tokens

Kemudian masukkan token baru ke aplikasi.

---

# ❌ Error GitHub 403

Contoh:

```text
403 Forbidden
```

Biasanya token tidak memiliki izin yang diperlukan.

Untuk classic PAT, pastikan scope yang diperlukan sudah dipilih, misalnya:

```text
repo
```

Jika menggunakan organisasi, kebijakan organisasi/SSO juga dapat membatasi token.

---

# ❌ Error GitHub 404 Saat Upload

Contoh:

```text
404 Not Found
```

Periksa beberapa hal berikut.

Pastikan repository benar:

```text
username/nama-repository
```

Contoh:

```text
yorukaizu-sudo/saweria-api-new
```

Pastikan branch benar:

```text
main
```

Buka repository di browser dan cek branch default-nya.

Repository tertentu mungkin memakai:

```text
master
```

bukan:

```text
main
```

Untuk private repository, pastikan token mempunyai akses ke repository tersebut.

Untuk classic PAT, biasanya dibutuhkan:

```text
repo
```

Untuk Fine-grained PAT, berikan repository access ke repository tujuan dan setidaknya:

```text
Contents: Read and write
Metadata: Read
```

---

# ❌ Error Branch Tidak Ditemukan

Contoh:

```text
Branch not found
```

Cek repository GitHub.

Pastikan nama branch sama persis.

Contoh:

```text
main
```

bukan:

```text
Main
```

---

# 🔐 Fine-Grained Personal Access Token

Selain classic PAT, GitHub juga menyediakan Fine-grained Personal Access Token.

Buka:

https://github.com/settings/personal-access-tokens/new

Pada:

```text
Repository access
```

pilih:

```text
All repositories
```

atau:

```text
Only select repositories
```

Jika menggunakan `Only select repositories`, pilih repository yang akan dikelola aplikasi.

Pada Repository Permissions, berikan sesuai kebutuhan. Untuk upload/edit/delete file repository:

```text
Contents
Read and write
```

Metadata biasanya tersedia sebagai:

```text
Metadata
Read-only
```

Gunakan permission tambahan hanya jika fitur aplikasi memang membutuhkannya.

---

# 🔒 Keamanan Token

GitHub Token sama sensitifnya dengan password.

JANGAN lakukan ini:

```python
TOKEN = "ghp_xxxxxxxxxxxxxxxxx"
```

Jangan masukkan token ke:

```text
github_uploader.py
README.md
config.py
GitHub repository
Discord
Telegram
Screenshot
```

Jika token terlanjur tersebar, segera buka:

https://github.com/settings/tokens

Kemudian:

```text
Revoke
```

token tersebut dan buat token baru.

---

# 🏗️ Build Menjadi EXE

Jika tidak ingin menjalankan:

```cmd
python github_uploader.py
```

aplikasi dapat di-build menjadi `.exe`.

Install PyInstaller:

```cmd
pip install pyinstaller
```

Masuk ke folder project:

```cmd
cd C:\Users\yoruk\Documents\TESTER
```

Build:

```cmd
pyinstaller --onefile --windowed --name GitHubUploader github_uploader.py
```

Tunggu sampai selesai.

Hasilnya berada di:

```text
dist\
```

Contoh:

```text
C:\Users\yoruk\Documents\TESTER\dist\GitHubUploader.exe
```

Jalankan:

```cmd
dist\GitHubUploader.exe
```

---

# 🖼️ Build EXE dengan Icon

Siapkan:

```text
icon.ico
```

Kemudian:

```cmd
pyinstaller --onefile --windowed --icon=icon.ico --name GitHubUploader github_uploader.py
```

Hasil:

```text
dist\GitHubUploader.exe
```

---

# 📦 Build EXE + tkinterdnd2

Jika menggunakan Drag & Drop dan hasil EXE mengalami masalah menemukan `tkinterdnd2`, coba:

```cmd
pyinstaller --noconfirm --clean --onefile --windowed --collect-all tkinterdnd2 --name GitHubUploader github_uploader.py
```

Dengan icon:

```cmd
pyinstaller --noconfirm --clean --onefile --windowed --collect-all tkinterdnd2 --icon=icon.ico --name GitHubUploader github_uploader.py
```

---

# 🧹 Clean Build

Untuk menghapus build lama:

```cmd
rmdir /s /q build
rmdir /s /q dist
del GitHubUploader.spec
```

Kemudian build ulang:

```cmd
pyinstaller --noconfirm --clean --onefile --windowed --collect-all tkinterdnd2 --name GitHubUploader github_uploader.py
```

---

# 🧪 Quick Installation

Jika Python sudah terinstall, cukup jalankan:

```cmd
cd C:\Users\yoruk\Documents\TESTER
pip install PyGithub tkinterdnd2 pyinstaller
python github_uploader.py
```

---

# 📌 Contoh Workflow Lengkap

Misalnya Anda mempunyai project:

```text
C:\Users\yoruk\Documents\MY-WEB
```

Repository tujuan:

```text
yorukaizu-sudo/my-web
```

Workflow:

```text
1. Jalankan GitHub Uploader
2. Masukkan GitHub Token
3. Klik Connect
4. Drag folder MY-WEB
5. Pilih yorukaizu-sudo/my-web
6. Pilih branch main
7. Isi commit message
8. Klik UPLOAD FOLDER TO GITHUB
9. Tunggu progress 100%
10. Selesai
```

Untuk menjalankan aplikasinya:

```cmd
cd C:\Users\yoruk\Documents\TESTER
python github_uploader.py
```

Setelah project diperbarui, cukup jalankan uploader kembali dan upload ke repository yang sama.

File yang sudah ada akan diperbarui dan file baru akan ditambahkan.

---

# 📚 Contoh Commit Message

Upload pertama:

```text
Initial project upload
```

Update:

```text
Update application
```

Bug fix:

```text
Fix API connection
```

Tambah fitur:

```text
Add authentication feature
```

Update UI:

```text
Improve user interface
```

Production:

```text
Production update v1.2.0
```

---

# ✅ Selesai

Sekarang Anda dapat mengelola repository GitHub menggunakan GUI tanpa harus melakukan command Git secara manual.

Untuk menjalankan aplikasi:

```cmd
python github_uploader.py
```

Untuk build EXE:

```cmd
pyinstaller --noconfirm --clean --onefile --windowed --collect-all tkinterdnd2 --name GitHubUploader github_uploader.py
```

Hasil EXE:

```text
dist\GitHubUploader.exe
```

Happy Coding! 🚀