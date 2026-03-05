from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt
from models import Base, get_db 
from models import (
    User, Ticket, Conversation, Message, SupportGroup, 
    Base, get_db  );


from sqlalchemy import text

from passlib.context import CryptContext

from fastapi.responses import Response

from sqlalchemy import desc
import uuid

app_sessions = {} 

from typing import Optional
from pydantic import BaseModel,field_validator


SECRET_KEY = "your-super-secret-key-change-in-prod"  # Global
ALGORITHM = "HS256"

from jose import JWTError, jwt
from openai import OpenAI
from difflib import get_close_matches
import os
import json
from pydantic import BaseModel, EmailStr

from models import  Message
from typing import List, Optional
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.security import (
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    get_password_hash,
)

from models.user import User
from models.ticket import Ticket
from models.conversation import Conversation
from models.messages import Message
from models.SupportGroup import SupportGroup

from categories import CATEGORIES

app = FastAPI()


app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




# ---------- GLOBAL EXCEPTION HANDLERS ----------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🚨 GLOBAL ERROR: {repr(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error - please contact support"},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Keep HTTPException JSON, just make sure it's JSON not HTML
    print(f"🚨 HTTP ERROR {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# ---------- Pydantic Models ----------
# ---------- Pydantic Models ----------
class SignupRequest(BaseModel):
    name: str
    email: str
    store_id: int
    role: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v


# ---------- Normalization helpers ----------
VALID_INTENTS = {"chat", "issue", "status_check", "close_ticket"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_DEPARTMENTS = {
    "IT",
    "HR",
    "LPD",
    "Operations",
    "Projects",
    "Marketing",
    "Property",
    "HG_Merchandising",
}

GREETING_WORDS = {
    "hi",
    "hello",
    "hey",
    "hii",
    "hlo",
    "yo",
    "sup",
    "thanks",
    "thank you",
    "ok",
    "okay",
    "bye",
    "goodbye",
}

def map_category(raw: str | None) -> str:
    if not raw:
        return "Operations - Customer Related"
    if raw in CATEGORIES:
        return raw
    match = get_close_matches(raw, CATEGORIES, n=1, cutoff=0.5)
    if match:
        return match[0]
    return "Operations - Customer Related"

def normalize_result(result: dict) -> dict:
    intent = result.get("intent", "chat")
    if intent not in VALID_INTENTS:
        intent = "chat"

    priority = result.get("priority") or "Medium"
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    department = result.get("department") or "Operations"
    if department not in VALID_DEPARTMENTS:
        department = "Operations"

    category = map_category(result.get("category"))

    result["intent"] = intent
    result["priority"] = priority
    result["department"] = department
    result["category"] = category
    return result

# ---------- Auth helper ----------


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 🔥 Get session from cookie (auto-sent by browser)
    session_id = request.cookies.get("session_id")
    
    if session_id and session_id in app_sessions:
        email = app_sessions[session_id]
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"✅ SESSION AUTH: {user.email} ({user.role})")
            return user
    
    print("❌ NO SESSION - Guest user")
    return User(email="guest@store.com", role="guest", name="Guest", id=1, store_id=1)

# ---------- Support group helpers ----------
def find_best_group(store_id: int, ticket_category: str, db: Session):
    try:
        query = """
        SELECT * FROM support_groups 
        WHERE store_id = :store_id 
        AND category ILIKE :category
        AND is_active = true
        ORDER BY id DESC LIMIT 1
        """
        result = db.execute(
            text(query),
            {"store_id": store_id, "category": f"%{ticket_category}%"},
        ).fetchone()
        return result
    except Exception as e:
        print("find_best_group error:", e)
        return None

def find_existing_open_ticket(db: Session, user_id: int, category: str):
    return (
        db.query(Ticket)
        .filter(
            Ticket.created_by == user_id,
            Ticket.category == category,
            Ticket.status.in_(["Open", "Assigned", "In Progress"]),
        )
        .order_by(Ticket.id.desc())
        .first()
    )

# ---------- Page routes ----------
@app.get("/debug")
async def debug(request: Request, current_user: User = Depends(get_current_user)):
    return {
        "role": current_user.role,
        "email": current_user.email,
        "referer": request.headers.get("referer", "none")
    }

@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request, current_user: User = Depends(get_current_user)):
    print(f"🔍 POST-LOGIN → Role: {current_user.role}, Email: {current_user.email}")
    
    if current_user.role == "guest":
        print("→ login.html (guest)")
        return templates.TemplateResponse("login.html", {"request": request})
    
    # 🔥 SMART ROLE-BASED DASHBOARD ROUTING
    if current_user.role == "admin":
        print("→ admin-dashboard.html")
        # 🔥 TEMP FIX - Use your existing endpoint
        db: Session = next(get_db())
        stats = {
            "totalTickets": db.query(Ticket).count(),
            "openTickets": db.query(Ticket).filter(Ticket.status.in_(["Open", "Assigned"])).count()
        }
        return templates.TemplateResponse("admin-dashboard.html", {
            "request": request,
            "total_tickets": stats.get("totalTickets", 0),
            "open_tickets": stats.get("openTickets", 0),
            "user": current_user
        })
    elif current_user.role in  ["engineer", "support"]:
        print("→ engineer_dashboard.html")
        return templates.TemplateResponse("engineer_dashboard.html", {
            "request": request,
            "user": current_user
        })
    else:  # manager, support, etc.
        print("→ home.html (manager)")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "user": current_user
        })


# Handle POST too (form submits)
@app.post("/", response_class=HTMLResponse)
async def root_post(request: Request, current_user: User = Depends(get_current_user)):
    return await root_page(request, current_user)

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
# 🔥 ADD THESE ROUTES (after your existing routes)

@app.get("/engineer-dashboard", response_class=HTMLResponse)
async def engineer_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["engineer", "support"]:
        raise HTTPException(status_code=403, detail="Engineer/Support access only")
    print("✅ ENGINEER DASHBOARD ROUTE HIT!")
    return templates.TemplateResponse("engineer_dashboard.html", {"request": request, "user": current_user})

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    print("✅ ADMIN DASHBOARD ROUTE HIT!")
    return templates.TemplateResponse("admin-dashboard.html", {"request": request, "user": current_user})



@app.get("/chat-ui")
@app.get("/dashboard")
async def user_dashboard(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user,
            "is_admin": user.role == "admin",
        },
    )

@app.get("/my-tickets", response_class=HTMLResponse)
def my_tickets_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "my-tickets.html",
        {
            "request": request,
            "user": user,
        },
    )

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
     return Response(status_code=204)

# ---------- Auth APIs ----------
@app.post("/api/signup")
async def signup(
    name: str = Form(...),
    email: str = Form(...),
    storeId: str = Form(...),  # ✅ String!
    role: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    print(f"🔍 FormData: name={name}, email={email}, storeId='{storeId}', role={role}")
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=name,
        email=email,
        store_id=storeId,  # ✅ 'store3' as-is!
        role=role,  # ✅ Full "manager"
        password=pwd_context.hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ CREATED: {user.email} role={user.role} store_id='{user.store_id}'")

    return {
        "access_token": "signup-success",
        "role": user.role,
        "message": "Success! Please login."
    }

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    password = form_data.password
    
    print(f"🔍 Login: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(401, "Invalid credentials")
    
    session_id = str(uuid.uuid4())
    app_sessions[session_id] = user.email
    
    # Role-based dashboard
    if user.role == "admin":
        dashboard_url = "/admin-dashboard"
    elif user.role in ["engineer", "support"]:
        dashboard_url = "/engineer-dashboard"
    else:
        dashboard_url = "/"
    
    response = JSONResponse({
        "success": True,
        "access_token": "session-cookie-set",  
        "role": user.role,
        "dashboard": dashboard_url
    })
    response.set_cookie(
    key="session_id", 
    value=session_id, 
    httponly=True, 
    max_age=3600 
)
    print(f"✅ LOGIN SUCCESS {user.email} ({user.role}) → {dashboard_url}")
    return response




# ---------- Engineer APIs ----------
@app.get("/api/engineer/tickets")
async def get_engineer_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["engineer", "support"]:
                  raise HTTPException(status_code=403, detail="Engineer access only")

    print(f"🔍 ENGINEER: {current_user.email} store_id={getattr(current_user, 'store_id', 'NONE')}")
    
    tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["Open", "Assigned", "In Progress"]))
        .order_by(Ticket.id.desc())
        .limit(20)
        .all()
    )
    
    result = []
    for t in tickets:
        created_by_user = getattr(t, 'created_by', 0)
        created_at_str = str(created_by_user) if isinstance(created_by_user, (int, str)) else "Unknown"
        
        result.append({
            "id": getattr(t, 'id', 0),
            "title": getattr(t, 'category', 'No Category'),
            "description": (
                (str(getattr(t, 'description', ''))[:100] + "...") 
                if len(str(getattr(t, 'description', ''))) > 100 
                else str(getattr(t, 'description', ''))
            ),
            "priority": getattr(t, "priority", "Medium"),
            "status": getattr(t, "status", "Open"),
            "store_id": getattr(t, "store_id", 1),
            "created_at": created_at_str,  # SAFE string
            "assigned_to": getattr(t, "assigned_to", "Unassigned"),
        })
    
    print(f"📊 Engineer returning {len(result)} ALL-STORES tickets")
    return result


@app.post("/api/engineer/update-status")
async def update_ticket_status(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket_id = request.get("ticket_id")
    status = request.get("status")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    ticket.assigned_to = f"{current_user.email} ({current_user.role})"
    db.commit()

    return {"success": True, "ticket_id": ticket_id, "status": status}

# ---------- Auto-assign APIs ----------
@app.get("/api/tickets/unassigned")
async def get_unassigned_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tickets = db.query(Ticket).filter(Ticket.status == "Open").all()
    return [
        {
            "id": t.id,
            "title": t.category or "No Category",
            "category": t.category,
            "store_id": t.store_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets
    ]

@app.post("/api/tickets/auto-assign")
async def auto_assign_ticket(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket_id = request.get("ticket_id")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return {"success": False, "error": "Ticket not found"}

    best_group = find_best_group(ticket.store_id, ticket.category, db)

    if best_group:
        ticket.status = "Assigned"
        ticket.assigned_to = best_group.group_name
        if hasattr(ticket, "assigned_group_id"):
            ticket.assigned_group_id = best_group.id

        db.commit()
        return {
            "success": True,
            "assigned_to": best_group.group_name,
            "group_id": best_group.id,
        }

    return {"success": False, "reason": "No matching group found"}

# ---------- My Tickets API ----------
@app.get("/api/my-tickets")
def get_my_store_tickets(
    status_filter: str = "All",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store_id = getattr(current_user, "store_id", None)
    if store_id is None:
        raise HTTPException(status_code=400, detail="Store not found for user")
    
    
    
    print(f"🔍 Querying store_id='{store_id}'")  # ✅ 'store3'
    
    query = db.query(Ticket).filter(Ticket.store_id == store_id)  # ✅ Direct match!
    
    if status_filter != "All":
        query = query.filter(Ticket.status == status_filter)

    tickets = query.order_by(Ticket.id.desc()).all()
    tickets_data = [
        {
            "id": t.id,
            "title": t.category or "No Category",
            "description": t.description or "",
            "priority": getattr(t, "priority", "Medium"),
            "status": getattr(t, "status", "Open"),
            "department": (
                t.category.split(" - ")[0]
                if t.category and " - " in t.category
                else (t.department or "Operations")
            ),
            "store_id": t.store_id,
            "ticket_number": getattr(t, "ticket_number", None),
            "image": getattr(t, "image", None),
            "created_at": t.created_at.isoformat()
            if getattr(t, "created_at", None)
            else None,
        }
        for t in tickets
    ]

    return {
        "store_name": store_id.replace('store', 'Store '),
        "role": current_user.role,  # 🔥 NEW: Send role to frontend
        "user_email": current_user.email,
        "tickets": tickets_data,
    }

# ---------- Support group admin ----------
@app.get("/api/admin/groups")
def get_groups(db: Session = Depends(get_db)):
    groups = db.query(SupportGroup).filter(SupportGroup.is_active == True).all()
    return [
        {
            "id": g.id,
            "store_id": g.store_id,
            "group_name": g.group_name,
            "category": g.category,
            "members": g.members,
            "member_count": len(json.loads(g.members)),
        }
        for g in groups
    ]

@app.post("/api/admin/groups")
def create_group(
    store_id: str = Form(...),
    group_name: str = Form(...),
    category: str = Form(...),
    members: str = Form(...),
    db: Session = Depends(get_db),
):
    members_list = [m.strip() for m in members.split(",")]

    group = SupportGroup(
        store_id=store_id,
        group_name=group_name,
        category=category,
        members=json.dumps(members_list),
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    return {"success": True, "message": "Group created!"}

# ---------- Admin APIs ----------
@app.get("/api/admin/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(Ticket).count()
    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["Open", "Assigned"]))
        .count()
    )
    resolved = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["Resolved", "Closed"]))
        .count()
    )
    active_stores = db.query(Ticket.store_id).distinct().count()

    return {
        "totalTickets": total,
        "openTickets": open_tickets,
        "resolvedTickets": resolved,
        "totalStores": active_stores,
    }

@app.get("/api/admin/tickets")
def get_admin_tickets(
    search: str = "",
    status_filter: str = "All",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Ticket)

    if search:
        like = f"%{search}%"
        query = query.filter(
            getattr(Ticket, "category", Ticket.id).ilike(like)
            | getattr(Ticket, "description", Ticket.id).ilike(like)
        )

    if status_filter != "All":
        query = query.filter(
            getattr(Ticket, "status", Ticket.id) == status_filter
        )

    tickets = query.order_by(getattr(Ticket, "id", Ticket.id).desc()).all()

    result = []
    for t in tickets:
        result.append(
            {
                "id": t.id,
                "title": getattr(t, "category", "No Category"),
                "description": getattr(t, "description", ""),
                "priority": getattr(t, "priority", "Medium"),
                "status": getattr(t, "status", "Open"),
                "department": t.department or "Operations",
                "store_id": getattr(t, "store_id", 1),
                "ticket_number": getattr(t, "ticket_number", None),
                "image": getattr(t, "image", None),
                "city": "Bengaluru",
                "assigned_to": getattr(t, "assigned_to", "Team IT"),
            }
        )

    return result

class ChatRequest(BaseModel):
    content: str

@app.post("/api/send-message")
def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = request.content.strip()
    if len(content) < 1:
        raise HTTPException(status_code=400, detail="Empty message")

    # Get real store_id from user (fallback to "demo")
    store_id = str(getattr(current_user, "store_id", "demo"))

    # Save USER message
    user_msg = Message(
        store_id=store_id,
        role="user",
        content=content,
    )
    db.add(user_msg)

    # Simple AI response (you can improve later)
    ai_response = f"Got your message: '{content[:50]}...' for store {store_id}."
    issue_detected = False
    category = None

    if "issue" in content.lower() or "problem" in content.lower():
        issue_detected = True
        category = "Operations - Customer Related"
        open_tickets = db.query(Ticket).filter(
            Ticket.store_id == store_id,
            Ticket.status.in_(["Open", "In Progress"])
        ).count()
        ai_response += f" You have {open_tickets} open tickets. Check /my-tickets."

    # Save AI message
    ai_msg = Message(
        store_id=store_id,
        role="assistant",
        content=ai_response,
    )
    db.add(ai_msg)
    db.commit()

    return {
        "status": "sent",
        "ai_response": ai_response,
        "issue_detected": issue_detected,
        "category": category,
    }    
def get_store_id():
    """Safe store_id STRING for chat - DEFINITION"""
    try:
        user = get_current_user()  # Your existing function
        if hasattr(user, 'store_id'):
            store_value = user.store_id
            print(f"🔍 Store ID: '{store_value}' (type: {type(store_value)})")
            return str(store_value)  # Always STRING
        print("🔍 No store_id, using demo")
        return "demo"
    except Exception as e:
        print(f"❌ Auth error: {e}, using demo")
        return "demo"

from sqlalchemy import text  # Add this import if missing

from sqlalchemy import text  # Add at top if missing

@app.get("/api/chat-history")
def get_chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = getattr(current_user, "id", 1)
    
    # 🔥 YOUR EXACT TABLE STRUCTURE
    convos = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.id.asc()).all()
    
    messages = []
    for convo in convos:
        messages.append({
            "role": "user" if convo.role == "user" else "bot",
            "content": convo.message[:300],  # Shorten long ones
            "timestamp": f"{convo.id}"  # Use ID as timestamp
        })
    
    return {
        "messages": messages,
        "store_name": getattr(current_user, 'store_id')
    }


# ---------- Chat & ticket creation ----------
def analyze_message_llm(message: str, db: Session, user_id: int) -> dict:
    history = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.id.desc())
        .limit(10)
        .all()
    )

    categories_text = "\n".join([f"- {cat}" for cat in CATEGORIES])

    system_prompt = f"""You are a friendly store support assistant that answers ALL questions.

ANSWER EVERY QUESTION naturally:
- Store hours, shifts, procedures, POS help, etc. = normal helpful answers
- ONLY "issue" for BROKEN THINGS: AC not working, printer broken, stock missing

Categories for issues only:
{categories_text}

Examples:
"what time do we open?" → intent: "chat", reply: "Stores open at 9 AM..."
"how do I check shift?" → intent: "chat", reply: "Check HR portal or ask manager"
"printer not working" → intent: "issue", category: "IT - Hardware - Printer Issue"

Always return JSON:
{{"intent": "chat", "reply": "Store opens 9AM...", "category": null,
  "priority": "Medium", "department": "Operations", "ticket_number": null}}"""

    messages = [{"role": "system", "content": system_prompt}]

    for h in reversed(history):
        messages.append({"role": h.role, "content": h.message})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        raw = json.loads(content)
    except Exception:
        raw = {
            "intent": "chat",
            "reply": "I'm here to assist you. How can I help?",
            "category": "Operations - Customer Related",
            "priority": "Medium",
            "department": "Operations",
            "ticket_number": None,
        }

    return normalize_result(raw)

@app.post("/chat")
def chat(
    message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = getattr(current_user, "id", 1)

    db.add(
        Conversation(
            user_id=user_id,
            message=message,
            role="user",
        )
    )
    db.commit()

    message_lower = message.strip().lower()
    if message_lower in GREETING_WORDS:
        reply = "Hello! How can I help you with your store issues today?"
        db.add(
            Conversation(
                user_id=user_id,
                message=reply,
                role="assistant",
            )
        )
        db.commit()
        return {"type": "chat", "message": reply}

    result = analyze_message_llm(message, db, user_id)
    intent = result.get("intent", "chat")

    if intent == "chat":
        reply = result.get("reply", "I'm here to assist you.")
        db.add(
            Conversation(
                user_id=user_id,
                message=reply,
                role="assistant",
            )
        )
        db.commit()
        return {"type": "chat", "message": reply}

    if intent == "issue":
        category = result["category"]
        priority = result["priority"]
        department = result["department"]

        existing = find_existing_open_ticket(db, user_id, category)
        if existing:
            reply = (
                f"You already raised a ticket for this issue: "
                f"{existing.ticket_number or existing.id}. "
                f"We'll update you once it is resolved."
            )
            db.add(
                Conversation(
                    user_id=user_id,
                    message=reply,
                    role="assistant",
                )
            )
            db.commit()
            return {
                "type": "chat",
                "message": reply,
                "ticket_number": existing.ticket_number,
                "already_exists": True,
            }

        reply = (
            f"I detected a {category} issue. Please upload an image or type 'skip' to create ticket."
        )

        return {
            "type": "issue_detected",
            "category": category,
            "priority": priority,
            "department": department,
            "message": reply,
            "already_exists": False,
        }

    return {
        "type": "chat",
        "message": "I'm not sure how to handle that. Could you rephrase?",
    }

@app.post("/create-ticket")
def create_ticket(
    description: str = Form(...),
    category: str = Form(...),
    priority: str = Form("Medium"),
    department: str = Form("Operations"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = getattr(current_user, "id", 1)
    
    # 🔥 FIX: Convert 'store2' → 2 (integer)
    store_id_int = int(current_user.store_id.replace('store', ''))
    print(f"🚨 FIXED: store_id='{current_user.store_id}' → {store_id_int}")

    existing = find_existing_open_ticket(db, user_id, category)
    if existing:
        msg = (
            f"You already raised a ticket for this issue: "
            f"{existing.ticket_number or existing.id}. "
            f"Please resolve/close that ticket before creating a new one."
        )

        db.add(
            Conversation(
                user_id=user_id,
                message=msg,
                role="assistant",
            )
        )
        db.commit()

        return {
            "already_exists": True,
            "ticket_number": existing.ticket_number,
            "message": msg,
        }

    image_path = None

    if file:
        os.makedirs("uploads", exist_ok=True)
        file_location = os.path.join("uploads", file.filename)
        with open(file_location, "wb") as buffer:
            buffer.write(file.file.read())
        image_path = file_location

    new_ticket = Ticket(
        category=category,
        description=description,
        store_id=store_id_int,  # ✅ FIXED: Use integer
        created_by=user_id,
        status="Open",
        priority=priority,
        department=department,
        image=image_path,
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    prefix = category.split("-")[0].strip()
    ticket_number = f"{prefix}-{str(new_ticket.id).zfill(4)}"
    new_ticket.ticket_number = ticket_number
    db.commit()

    db.add(
        Conversation(
            user_id=user_id,
            message=f"Ticket {ticket_number} created and previous issue is logged.",
            role="assistant",
        )
    )
    db.commit()

    return {"ticket_number": ticket_number, "already_exists": False}