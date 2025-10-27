from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import redis
import time

app = Flask(__name__, static_folder="static", template_folder="templates")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

TASK_ID_KEY = "task:id"
TASK_SET_KEY = "tasks"
VALID_STATUSES = ["todo", "inprogress", "done"]

def task_key(task_id):
    return f"task:{task_id}"

def create_task(title, description, tags=None):
    tid = r.incr(TASK_ID_KEY)
    now = int(time.time())
    mapping = {
        "id": tid,
        "title": title,
        "description": description or "",
        "status": "todo",
        "created_at": now,
        "tags": ",".join(tags) if tags else ""
    }
    r.hset(task_key(tid), mapping=mapping)
    r.sadd(TASK_SET_KEY, tid)
    return tid

def get_task(tid):
    t = r.hgetall(task_key(tid))
    # convert id and created_at to ints if present
    if t:
        t["id"] = int(t["id"])
        t["created_at"] = int(t.get("created_at", 0))
        # convert tags to list
        t["tags"] = t.get("tags","").split(",") if t.get("tags","") else []
    return t

def get_all_tasks():
    ids = r.smembers(TASK_SET_KEY)
    tasks = []
    for tid in ids:
        t = get_task(tid)
        if t:
            tasks.append(t)
    tasks.sort(key=lambda x: x.get("created_at", 0))
    return tasks

def update_task_status(tid, status):
    if status not in VALID_STATUSES:
        return False
    key = task_key(tid)
    if not r.exists(key):
        return False
    r.hset(key, "status", status)
    return True

def delete_task(tid):
    r.delete(task_key(tid))
    r.srem(TASK_SET_KEY, tid)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/board")
def board():
    return render_template("board.html")

# JSON API endpoints for frontend

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    tasks = get_all_tasks()
    # group by status for convenience
    grouped = {"todo": [], "inprogress": [], "done": []}
    for t in tasks:
        grouped.setdefault(t.get("status", "todo"), []).append(t)
    return jsonify(grouped)

@app.route("/api/task", methods=["POST"])
def api_add_task():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    tags = data.get("tags", [])
    if not title:
        return jsonify({"error": "title required"}), 400
    tid = create_task(title, description, tags)
    task = get_task(tid)
    return jsonify(task), 201

@app.route("/api/move", methods=["POST"])
def api_move_task():
    data = request.get_json() or {}
    tid = data.get("id")
    status = data.get("status")
    if tid is None or status is None:
        return jsonify({"error": "id and status required"}), 400
    # Redis stores ids as ints or strings; ensure str
    ok = update_task_status(str(tid), status)
    if not ok:
        return jsonify({"error": "invalid id or status"}), 400
    return jsonify({"ok": True})

@app.route("/api/delete", methods=["POST"])
def api_delete_task():
    data = request.get_json() or {}
    tid = data.get("id")
    if tid is None:
        return jsonify({"error": "id required"}), 400
    delete_task(str(tid))
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

