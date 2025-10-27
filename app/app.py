from flask import Flask, render_template, request, redirect, url_for
import os
import redis
import time

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# Helper keys
TASK_ID_KEY = "task:id"         # INCR counter
TASK_SET_KEY = "tasks"          # set of task ids

VALID_STATUSES = ["todo", "inprogress", "done"]

def task_key(task_id):
    return f"task:{task_id}"

def create_task(title, description):
    tid = r.incr(TASK_ID_KEY)
    now = int(time.time())
    r.hset(task_key(tid), mapping={
        "id": tid,
        "title": title,
        "description": description,
        "status": "todo",
        "created_at": now
    })
    r.sadd(TASK_SET_KEY, tid)
    return tid

def get_task(tid):
    return r.hgetall(task_key(tid))

def get_all_tasks():
    ids = r.smembers(TASK_SET_KEY)
    tasks = []
    for tid in ids:
        t = get_task(tid)
        if t:
            tasks.append(t)
    # sort by created_at asc
    tasks.sort(key=lambda x: int(x.get("created_at", 0)))
    return tasks

def update_task_status(tid, status):
    if status not in VALID_STATUSES:
        return False
    if not r.exists(task_key(tid)):
        return False
    r.hset(task_key(tid), "status", status)
    return True

def delete_task(tid):
    r.delete(task_key(tid))
    r.srem(TASK_SET_KEY, tid)

@app.route("/")
def index():
    tasks = get_all_tasks()
    columns = {"todo": [], "inprogress": [], "done": []}
    for t in tasks:
        status = t.get("status", "todo")
        columns[status].append(t)
    return render_template("index.html", columns=columns)

@app.route("/add", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if title:
            create_task(title, description)
        return redirect(url_for("index"))
    return render_template("add_task.html")

@app.route("/move/<tid>/<status>", methods=["POST"])
def move_task(tid, status):
    update_task_status(tid, status)
    return redirect(url_for("index"))

@app.route("/delete/<tid>", methods=["POST"])
def remove_task(tid):
    delete_task(tid)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
