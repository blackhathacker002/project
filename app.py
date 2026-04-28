from flask import Flask, render_template, request, redirect, session, flash
import os
import base64
from cryptography.fernet import Fernet
import json
import hashlib

# ================= USER STORAGE =================
USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ================= HASH =================
def generate_hash_id(phone):
    return hex(int(phone))[2:].upper()

# ================= META =================
META_FILE = "files/meta.json"

def load_meta():
    if not os.path.exists(META_FILE):
        return {}
    try:
        with open(META_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except:
        return {}

def save_meta(meta):
    os.makedirs("files", exist_ok=True)
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=4)

# ================= APP =================
app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= KEY =================
def generate_key(user_key):
    return base64.urlsafe_b64encode(user_key.ljust(32)[:32])

# ================= HOME =================
@app.route("/")
def home():
    # If the user has already seen the intro in this browser session,
    # skip straight to the landing page.
    if session.get("intro_seen"):
        return render_template("index.html", skip_intro=True)
    # First visit — show the enter/video screen and mark it as seen.
    session["intro_seen"] = True
    return render_template("index.html", skip_intro=False)

@app.route("/intro")
def intro():
    # Legacy route kept for compatibility — behaves same as first-time home
    session["intro_seen"] = True
    return render_template("index.html", skip_intro=False)

# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        users = load_users()

        email = request.form["email"]

        if email in users:
            flash("User already exists")
            return redirect("/")

        hash_id = generate_hash_id(request.form["phone"])

        users[email] = {
            "name": request.form["name"],
            "phone": request.form["phone"],
            "password": request.form["password"],
            "hash": hash_id
        }

        save_users(users)

        return render_template(
            "identity.html",
            hash_id=hash_id,
            password=request.form["password"]
        )

    return render_template("signup.html")

# ================= SIGNIN =================
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        users = load_users()

        for email, data in users.items():
            if data["hash"] == request.form["hash"]:
                session["user"] = email
                session["auth1"] = True
                return redirect("/password")

        session.clear()
        flash("Invalid Credentials")
        return redirect("/")

    return render_template("signin.html")

# ================= PASSWORD =================
@app.route("/password", methods=["GET", "POST"])
def password():
    if "auth1" not in session:
        return redirect("/")

    users = load_users()

    if request.method == "POST":
        email = session["user"]

        if users[email]["password"] == request.form["password"]:
            session["auth"] = True
            return redirect("/dashboard")
        session.clear()
        flash("Invalid Credentials")
        return redirect("/")

    return render_template("password.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "auth" not in session:
        return redirect("/")

    os.makedirs("files", exist_ok=True)

    files = os.listdir("files")
    meta = load_meta()

    file_data = []

    for f in files:
        if f == "meta.json":
            continue

        path = os.path.join("files", f)

        status = "Not Encrypted"

        if f in meta:
            status = meta[f].get("status", "Not Encrypted")
        else:
            try:
                with open(path, "rb") as file:
                    data = file.read(10)
                    if data.startswith(b"RSA_") or data.startswith(b"DES_"):
                        status = "Encrypted"
                    elif not data.isascii():
                        status = "Encrypted"
            except:
                status = "Unknown"

        try:
            file_time = os.path.getmtime(path)
        except:
            file_time = 0

        file_data.append({
            "name": f,
            "status": status,
            "time": file_time
        })

    file_data.sort(key=lambda x: x["time"], reverse=True)

    encrypted_count = len([f for f in file_data if f["status"] == "Encrypted"])
    decrypted_count = len([f for f in file_data if f["status"] != "Encrypted"])

    return render_template(
        "dashboard.html",
        files=file_data,
        total=len(file_data),
        encrypted_count=encrypted_count,
        decrypted_count=decrypted_count
    )

# ================= NEW =================
@app.route("/new")
def new():
    if "auth" not in session:
        return redirect("/")
    return render_template("editor.html")

# ================= SAVE =================
@app.route("/save", methods=["POST"])
def save():
    os.makedirs("files", exist_ok=True)

    filename = request.form["filename"] + ".txt"
    content = request.form["content"]

    path = os.path.join("files", filename)

    with open(path, "w") as f:
        f.write(content)

    meta = load_meta()
    meta[filename] = {"status": "Not Encrypted"}
    save_meta(meta)

    return redirect("/dashboard")

# ================= ENCRYPT =================
# ================= ENCRYPT =================
@app.route("/encrypt", methods=["GET", "POST"])
def encrypt():
    if request.method == "POST":
        os.makedirs("files", exist_ok=True)

        file = request.files["file"]
        algo = request.form["algo"]
        user_key = request.form["key"].encode()

        filename = file.filename
        path = os.path.join("files", filename)

        meta = load_meta()

        if filename in meta and meta[filename].get("status") == "Encrypted":
            flash("File is already encrypted")
            return redirect("/")

        data = file.read()

        # Store a hash of the key so we can verify it on decryption
        key_hash = hashlib.sha256(user_key).hexdigest()

        if algo == "AES":
            key = generate_key(user_key)
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data)
        elif algo == "DES":
            encrypted = b"DES_" + data[::-1]
        elif algo == "RSA":
            encrypted = b"RSA_" + data[::-1]

        with open(path, "wb") as f:
            f.write(encrypted)

        # Save key_hash alongside status and algo
        meta[filename] = {"status": "Encrypted", "algo": algo, "key_hash": key_hash}
        save_meta(meta)

        return redirect("/dashboard")

    return render_template("encrypt.html") 
# ================= DECRYPT =================
# ================= DECRYPT =================
@app.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    if request.method == "POST":
        file = request.files["file"]
        user_key = request.form["key"]
        data_to_decrypt = file.read()

        try:
            if data_to_decrypt.startswith(b"DES_"):
                # Hash the user key and compare against stored key hash
                stored_key_hash = load_meta().get(file.filename, {}).get("key_hash")
                input_key_hash = hashlib.sha256(user_key.encode()).hexdigest()

                if stored_key_hash and stored_key_hash != input_key_hash:
                    flash("Invalid Key")
                    return redirect("/")

                data = data_to_decrypt[4:][::-1]
                return render_template("output.html", data=data.decode("utf-8", errors="replace"))

            elif data_to_decrypt.startswith(b"RSA_"):
                stored_key_hash = load_meta().get(file.filename, {}).get("key_hash")
                input_key_hash = hashlib.sha256(user_key.encode()).hexdigest()

                if stored_key_hash and stored_key_hash != input_key_hash:
                    flash("Invalid Key")
                    return redirect("/")

                data = data_to_decrypt[4:][::-1]
                return render_template("output.html", data=data.decode("utf-8", errors="replace"))

            else:
                key = generate_key(user_key.encode())
                fernet = Fernet(key)
                data = fernet.decrypt(data_to_decrypt)  # raises on wrong key
                return render_template("output.html", data=data.decode("utf-8", errors="replace"))

        except Exception:
            flash("Invalid Key")
            return redirect("/")

    return render_template("decrypt.html") 

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/view/<path:filename>")
def view_file(filename):
    if "auth" not in session:
        return redirect("/")

    path = os.path.join("files", filename)

    if not os.path.exists(path):
        return "File not found"

    try:
        with open(path, "rb") as f:
            data = f.read()
        content = data.decode("utf-8", errors="replace")
    except Exception as e:
        content = "ERROR: " + str(e)

    return render_template("view.html", filename=filename, content=content)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True) 
