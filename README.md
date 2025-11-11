# 🚀 ReleaseTracker

A modern full‑stack web application to **track software releases**, **scan requirement files**, and **manage user accounts with role‑based access**.

Built with **Flask + Supabase (Backend)** and **React + Vite + Tailwind (Frontend)**, featuring secure **JWT authentication** and a strict **single‑admin policy**.kbk

---

## 📌 Key Highlights

* 🔐 **Role‑based Authentication** (Admin & User)
* 🛡️ **Single‑Admin Policy** — No promotions allowed
* 📦 **Requirements Scanner** — Import packages from a `requirements.txt`‑style file
* 🧑‍💼 **Admin Capabilities**:

  * View all users (roles are read‑only)
  * View all releases (global)
  * Create releases for self or any user
* 👤 **User Capabilities**:

  * View only their releases
  * Import packages from requirement files
  * Update & delete their own releases

---

## 🧰 Tech Stack

| Layer    | Technology                              |
| -------- | --------------------------------------- |
| Frontend | React, Vite, Tailwind CSS               |
| Backend  | Flask + Supabase REST API               |
| Auth     | JWT (role‑aware)                        |
| Roles    | `admin`, `user` (single‑admin enforced) |

---

## 📂 Project Structure

```
backend/
  routes/
    auth.py
    releases.py
  utils/
    auth.py
    supabase.py
  run_local.py
  .env

frontend/
  src/
    pages/        # Auth / Admin / Tracker pages
    components/   # Release list, forms, scanner
    lib/api.js
  index.html
  vite.config.js
```

---

## 🧑‍💻 Prerequisites

* Python **3.10+**
* Node.js **20.19+ or 22.12+** (required for Vite)
* Supabase Project (URL + Service Role Key)
* Ability to generate secrets:

### Generate Secrets

Using OpenSSL:

```bash
openssl rand -base64 32
```

Using Python:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔐 Environment Variables (`backend/.env`)

```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
PORT=8000
JWT_SECRET=<strong random secret>
JWT_EXP_SECONDS=86400
ADMIN_SIGNUP_SECRET=<optional | defaults to JWT_SECRET>
```

> ⚠️ **Keep `SUPABASE_SERVICE_ROLE_KEY` & `JWT_SECRET` private.**

---

## ⚙️ Installation & Run Instructions

### ✅ Backend (Flask)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run_local.py
# → http://localhost:8000
```

### 🎨 Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# open URL shown in terminal (e.g., http://localhost:5173)
```

---

## 🔑 Authentication & Role Logic

### 📝 Registration

* Default role = `user`
* To create **first & only admin**:

  * Enable **Register as Admin** checkbox
  * Enter **Admin Signup Secret**
* Once admin exists → further admin signups blocked

### 🔓 Login

* User chooses role at login (User/Admin)
* If selected role mismatches actual stored role → ❌ **403 Forbidden**

---

## 📡 API Reference (Backend)

Base URL: `http://localhost:8000`

### 🔐 Auth

| Method | Endpoint    | Description            |
| ------ | ----------- | ---------------------- |
| POST   | `/register` | Register user/admin    |
| POST   | `/login`    | Login as user/admin    |
| GET    | `/me`       | Get authenticated user |

#### `/register` Body

```json
{ "name": "", "email": "", "password": "", "role": "user", "admin_secret": "" }
```

Rules:

* If role = `admin`: `admin_secret` must match & no admin must already exist

#### `/login` Body

```json
{ "email": "", "password": "", "as_role": "admin/user" }
```

* If `as_role` mismatches stored role → **403**

---

### 🧑‍💼 Admin Endpoints (Require Admin Token)

| Method | Endpoint                     | Description                 |
| ------ | ---------------------------- | --------------------------- |
| GET    | `/admin/users`               | List all users              |
| PATCH  | `/admin/users/:user_id/role` | Change role (**user only**) |

> 🚫 Promotion to admin is blocked (single‑admin policy)

---

### 📦 Releases

| Method | Endpoint                | Access     | Description             |
| ------ | ----------------------- | ---------- | ----------------------- |
| GET    | `/releases`             | admin/user | admin → all, user → own |
| POST   | `/releases`             | admin      | Create release          |
| PATCH  | `/releases/:id`         | admin/user | admin → any, user → own |
| DELETE | `/releases/:id`         | admin/user | admin → any, user → own |
| POST   | `/releases/import-scan` | admin/user | Import scanned packages |

Import Rules:

* Admin checks duplicates **globally**
* User checks duplicates **within their releases only**

---

## 🧑‍🎨 Frontend UX

### Auth Page

* Signup with admin option + secret
* Login with role selection
* Role mismatch → error message

### Dashboard (User)

* Upload `requirements.txt` → scan + select packages to import
* View / Edit / Delete their releases

### Admin Panel

* View all users (roles locked)
* View all releases
* Create release for any user
* **Single‑admin reminder** with shield icon

### UI Enhancements

* Branded navbar with gradients & icons
* Admin tab shows badge for visibility

---

## 🔒 Security Notes

* Never expose `SUPABASE_SERVICE_ROLE_KEY` on frontend
* Admin secret should differ from JWT secret in production
* Role enforcement handled at backend, not UI

---

## 🧰 Troubleshooting

| Issue                    | Fix                                    |
| ------------------------ | -------------------------------------- |
| Port 8000 busy           | `lsof -i:8000` → kill PID              |
| Vite Node version error  | Upgrade Node to **20.19+ / 22.12+**    |
| Admin tab not visible    | Logout → Login again (token refresh)   |
| `/me` empty / wrong role | Ensure correct token passed in headers |

---

## 🛠️ Development Tips

* Restart backend after `.env` changes
* Check backend logs for Supabase API errors
* Test role mismatch intentionally to verify 403 behavior

---

## 📄 License

MIT (or your preferred license)

---

## 🤝 Contributing

Open a PR with:

* Clear feature description
* Reproduction steps if bug
* Follow existing code style

---

> ✅ **Summary**: README includes setup, env, roles, API, run steps, UX, and security aligned with current project behavior.
