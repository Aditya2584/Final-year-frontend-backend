# Healthcare Management System - Final Year Project
## Frontend & Backend Architecture Explanation

---

## 🎯 **Project Overview**

This is a **Smart Healthcare Management System** with two main components:
1. **Heartbeat Detection System** - Real-time heart rate monitoring using AI/CV
2. **Appointment Management System** - Doctor appointment booking & scheduling

---

## 📊 **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React/Vite)                   │
│                    (Port: 5173)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Navigation (Navbar)                                   │
│  ├─ Hero Section / Home Page                              │
│  ├─ Heartbeat Checker (Real-time video analysis)          │
│  ├─ Appointment Booking Form                              │
│  └─ Appointment Dashboard (View/Manage)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓↑
                    (HTTP/REST API)
                   CORS: localhost:5173
                           ↓↑
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│                    (Port: 8000)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Health Check Endpoint (/health)                       │
│  ├─ Heartbeat API                                          │
│  │  ├─ /api/heartbeat/start (POST)                        │
│  │  ├─ /api/heartbeat/result/{job_id} (GET)              │
│  │  ├─ /api/heartbeat/session/start (POST)               │
│  │  └─ /api/heartbeat/session/{id}/frame (POST)          │
│  │                                                         │
│  └─ Appointments API                                       │
│     ├─ /api/appointments (POST, GET)                      │
│     ├─ /api/appointments/{id} (GET, PUT, DELETE)          │
│     └─ /api/appointments/reschedule/{id} (PUT)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ↓↑
                    (Database Layer)
                           ↓↑
┌─────────────────────────────────────────────────────────────┐
│                    SQLAlchemy ORM                           │
│                  SQLite Database                            │
├─────────────────────────────────────────────────────────────┤
│  Tables:                                                    │
│  ├─ Appointments (id, full_name, phone, email, doctor...)  │
│  └─ Status tracking (pending, confirmed, completed)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 **FRONTEND - React Component Structure**

### **Technology Stack:**
- **Framework:** React 18 + Vite
- **Routing:** React Router
- **Styling:** Tailwind CSS
- **State Management:** React Hooks (useState, useEffect, useRef)

### **Key Components:**

#### 1. **App.jsx** (Main Router)
```
Routes:
├─ / (Home Page)
│  ├─ Navbar
│  ├─ Hero Section
│  ├─ Logo Strip
│  ├─ Steps
│  └─ Doctors
├─ /appointment (Booking Form)
└─ /appointments (Dashboard)
```

#### 2. **Heartbeat Checker Component**
**File:** `components/HeartbeatChecker.jsx`

**How it works:**
1. User clicks "Start Heartbeat Detection"
2. Frontend sends POST request: `/api/heartbeat/start`
   ```javascript
   {
     duration_sec: 15,
     camera_index: 0
   }
   ```
3. Backend responds with `job_id`
4. Frontend polls every 1 second: `/api/heartbeat/result/{job_id}`
5. Backend processes video frames & detects heart rate (BPM)
6. Results displayed with visualization (plot image)

**State Management:**
```javascript
status: idle | running | done | error
jobId: tracking the job
bpm: heart rate result
plotBase64: graph visualization
```

#### 3. **Appointment Booking Component**
**File:** `pages/AppointmentBooking.jsx`

**Form Fields:**
- Full Name (required)
- Phone Number (required)
- Email (optional)
- Reason for Visit (required)
- Doctor Selection (optional)
- Appointment Date (required)
- Appointment Time (fixed slots: 09:00, 09:30, 10:00... 17:00)

**Process:**
1. User fills form → validates locally
2. Sends POST: `/api/appointments`
3. Backend validates & stores in database
4. Frontend redirects to appointment dashboard on success

#### 4. **Appointment Dashboard Component**
**File:** `pages/AppointmentDashboard.jsx`

**Features:**
- View all booked appointments
- Reschedule appointments
- Cancel appointments
- Filter/search by date or doctor

---

## 🔧 **BACKEND - FastAPI Application**

### **Technology Stack:**
- **Framework:** FastAPI (Python async web framework)
- **Server:** Uvicorn ASGI server
- **Database ORM:** SQLAlchemy
- **Task Processing:** ThreadPoolExecutor (background jobs)
- **CV/AI:** OpenCV, NumPy, Matplotlib

### **Key Files:**

#### 1. **main.py** - API Server Setup
**Core Features:**
- CORS Configuration (allows frontend requests)
- Middleware setup
- Route registration
- Database initialization

**CORS Settings:**
```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
```

#### 2. **Heartbeat API Endpoints**

**A. Start Heartbeat Job:**
```
POST /api/heartbeat/start
Request:
{
  "duration_sec": 15,
  "camera_index": 0
}

Response:
{
  "job_id": "uuid-string",
  "status": "running"
}
```

**B. Get Result (Polling):**
```
GET /api/heartbeat/result/{job_id}

Response (while processing):
{
  "status": "processing",
  "bpm": null
}

Response (complete):
{
  "status": "done",
  "bpm": 72.5,
  "message": "Normal heart rate",
  "plot_png_base64": "iVBORw0KGgo...",
  "series": {...}
}
```

**How Heartbeat Detection Works:**
1. **Frame Capture:** Access user's webcam (camera_index: 0)
2. **Face Detection:** Haar Cascade classifier detects face
3. **Forehead ROI Extraction:** Extracts forehead region (brightest area)
4. **Signal Processing:**
   - Extract color signal (green channel most sensitive to blood)
   - Apply frequency filtering
   - Perform FFT (Fast Fourier Transform)
5. **BPM Calculation:** Find dominant frequency in 40-200 BPM range
6. **Visualization:** Generate graph of signal + frequency spectrum
7. **Result Return:** Base64 encode plot, return with metrics

**Key Backend File:** `api/heartbeat_service.py`
- `HeartbeatResult` dataclass stores: bpm, message, plot_png_base64, series
- `_make_plot_png_base64()` generates matplotlib graphs
- Uses `lib/processors.py` for signal processing
- Uses `lib/device.py` for camera access

#### 3. **Appointments API Endpoints**

**A. Create Appointment:**
```
POST /api/appointments
Request:
{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "email": "john@example.com",
  "reason": "Regular checkup",
  "doctor": "Dr. Smith",
  "appointment_date": "2026-05-15",
  "appointment_time": "10:30"
}

Response:
{
  "id": 1,
  "status": "pending",
  "booking_timestamp": "2026-05-08T14:30:00"
}
```

**B. Get All Appointments:**
```
GET /api/appointments
Response: List of appointment objects
```

**C. Get Single Appointment:**
```
GET /api/appointments/{id}
Response: Appointment details
```

**D. Reschedule:**
```
PUT /api/appointments/{id}/reschedule
Request:
{
  "appointment_date": "2026-05-20",
  "appointment_time": "14:00"
}
```

**E. Cancel:**
```
DELETE /api/appointments/{id}
```

**Validation Logic:**
- Phone number: minimum 10 digits
- Date/Time: must be future (not past)
- Required fields: full_name, phone, reason, date, time
- Time format: HH:MM (24-hour)

#### 4. **Database Models**

**File:** `api/models.py`

**Appointment Model:**
```python
class Appointment(Base):
    __tablename__ = "appointments"
    
    id: int (Primary Key)
    full_name: str (required)
    phone: str (required)
    email: str (optional)
    reason: str (required)
    doctor: str (optional)
    appointment_date: date (required)
    appointment_time: str (required, HH:MM format)
    status: AppointmentStatus (pending/confirmed/completed/cancelled)
    booking_timestamp: datetime (auto-set to now)
```

#### 5. **Database Layer**

**File:** `api/db.py`

**Features:**
- SQLite database (local, file-based: `heartbeat.db`)
- SQLAlchemy session management
- Dependency injection for database access

```python
# Frontend makes request
# → Backend route handler receives it
# → Injects db: Session dependency
# → Queries database
# → Returns response
```

---

## 🔄 **Data Flow - Complete Example**

### **Scenario 1: User Books an Appointment**

```
Frontend (React):
1. User fills form: John Doe, +12345678900, Regular checkup, 2026-05-15, 10:30
2. Form validation (frontend)
3. POST request to "http://localhost:8000/api/appointments"
4. Wait for response

Backend (FastAPI):
5. Receive POST request
6. Parse JSON using Pydantic model (AppointmentCreate)
7. Validate:
   - Phone has 10+ digits ✓
   - Date is future ✓
   - All required fields present ✓
8. Create Appointment object in database
9. Return 200 OK with appointment ID

Frontend (React):
10. Receive success response
11. Show success message
12. Redirect to appointment dashboard
13. Fetch updated appointments list
```

### **Scenario 2: User Checks Heart Rate**

```
Frontend (React):
1. User clicks "Start Heartbeat Detection"
2. POST to "/api/heartbeat/start" with duration_sec=15
3. Receive job_id from backend
4. Set status = "running"

Backend (FastAPI):
5. Create async job in ThreadPoolExecutor
6. Job runs in background:
   - Access user's webcam
   - Run for 15 seconds
   - Capture frames continuously
   - Process each frame:
     * Detect face using Haar Cascade
     * Extract forehead ROI
     * Extract color signal
     * Build signal array
   - After 15 seconds, process signal:
     * Filter noise
     * Compute FFT (Fast Fourier Transform)
     * Find dominant frequency
     * Convert to BPM
     * Generate plot image
7. Store result in memory

Frontend (React):
8. Poll every 1 second: GET "/api/heartbeat/result/{job_id}"
9. Backend returns: {"status": "processing", "bpm": null}
10. Keep polling...

Backend (After processing complete):
11. Store: {"status": "done", "bpm": 72.5, "plot_png_base64": "..."}

Frontend (React):
12. Poll response now includes BPM and plot
13. Set status = "done"
14. Display BPM: "72 BPM - Normal Heart Rate"
15. Display plot image (decoded from base64)
```

---

## 🚀 **How to Run the System**

### **Prerequisites:**
- Python 3.9+
- Node.js 16+
- Webcam access (for heartbeat feature)

### **Backend Setup:**
```bash
cd Backend
python -m venv venv
./venv/Scripts/Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### **Frontend Setup:**
```bash
cd Frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

**Backend running:** http://localhost:8000
**Frontend running:** http://localhost:5173

---

## 🔐 **Security & Best Practices**

### **Implemented:**
1. ✅ CORS restriction (only localhost:5173)
2. ✅ Input validation (Pydantic models)
3. ✅ Date/time validation (prevent past dates)
4. ✅ Phone number validation
5. ✅ HTTP error codes (400, 404, 500)
6. ✅ Request field limits (max lengths)
7. ✅ Database transactions (atomic operations)

### **Production Improvements (Future):**
1. Authentication/Authorization (JWT tokens)
2. Rate limiting (prevent abuse)
3. HTTPS/TLS encryption
4. Database encryption
5. Logging & monitoring
6. API versioning
7. Caching (Redis)

---

## 📊 **Key Technologies**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | React 18 | User interface |
| **Backend** | FastAPI | REST API server |
| **Database** | SQLite + SQLAlchemy | Data persistence |
| **Computer Vision** | OpenCV | Face detection, frame processing |
| **Signal Processing** | NumPy, SciPy | Heart rate calculation (FFT) |
| **Visualization** | Matplotlib | Generate plots |
| **Async Processing** | ThreadPoolExecutor | Background heartbeat jobs |
| **Web Server** | Uvicorn | ASGI server for FastAPI |
| **HTTP Client** | Fetch API | Frontend → Backend requests |
| **Routing** | React Router | Frontend navigation |
| **Styling** | Tailwind CSS | UI styling |

---

## 💡 **Key Learning Points**

### **Frontend:**
1. **Async/Await & Promises** - API communication
2. **React Hooks** - State management (useState, useEffect, useRef)
3. **Component Composition** - Reusable UI components
4. **Polling Pattern** - Regular backend queries
5. **Form Validation** - Client-side data integrity

### **Backend:**
1. **REST API Design** - Proper HTTP methods & status codes
2. **Request/Response Validation** - Pydantic models
3. **Database ORM** - SQLAlchemy abstraction
4. **Async Background Tasks** - ThreadPoolExecutor
5. **CORS Middleware** - Cross-origin requests
6. **Signal Processing** - FFT, frequency analysis
7. **Computer Vision** - Face detection with OpenCV

### **Full-Stack Integration:**
1. **Client-Server Architecture**
2. **Data Serialization** - JSON format
3. **Error Handling** - HTTP status codes
4. **State Management** - Frontend ↔ Backend synchronization
5. **Real-time Updates** - Polling mechanism
6. **Security** - CORS, input validation

---

## 🎓 **Presentation Talking Points**

### **Opening:**
> "This is a smart healthcare management system that combines computer vision technology for heartbeat detection with a practical appointment booking system. The architecture demonstrates a complete client-server application with real-time processing."

### **Technical Highlights:**
1. **Heartbeat Detection** - Advanced signal processing using FFT
2. **RESTful API** - Clean separation of concerns
3. **Real-time Polling** - Responsive user experience
4. **Database Design** - Normalized schema for appointments
5. **CORS Security** - Protected cross-origin requests

### **Challenges Overcome:**
1. Real-time video processing with minimal latency
2. Accurate heart rate calculation from webcam
3. Handling concurrent user requests
4. Frontend-backend synchronization

### **Future Enhancements:**
1. WebSocket for real-time updates
2. User authentication & history
3. Doctor dashboard for appointment management
4. Mobile app (React Native)
5. Cloud deployment
6. Advanced analytics

---

## 📁 **File Structure Summary**

```
Backend/
├── api/
│   ├── main.py (FastAPI app, routes)
│   ├── heartbeat_service.py (BPM calculation)
│   ├── frame_session.py (Session management)
│   ├── appointments.py (CRUD endpoints)
│   ├── models.py (SQLAlchemy ORM models)
│   ├── db.py (Database connection)
│   └── __init__.py
├── lib/
│   ├── device.py (Camera access)
│   ├── processors.py (Signal processing)
│   ├── interface.py (Data structures)
│   └── __init__.py
├── requirements.txt (Dependencies)
└── README.md

Frontend/
├── src/
│   ├── App.jsx (Main router)
│   ├── main.jsx (React entry point)
│   ├── components/
│   │   ├── HeartbeatChecker.jsx
│   │   ├── HeartbeatResults.jsx
│   │   └── HeartbeatScanModal.jsx
│   ├── pages/
│   │   ├── AppointmentBooking.jsx
│   │   └── AppointmentDashboard.jsx
│   ├── sections/
│   │   ├── Navbar.jsx
│   │   ├── Hero.jsx
│   │   ├── Steps.jsx
│   │   └── ...other sections
│   ├── api/
│   │   ├── appointments.js (API calls)
│   │   └── ...
│   ├── package.json (Dependencies)
│   └── vite.config.js (Build config)
```

---

## ✅ **Conclusion**

This project demonstrates a complete full-stack application with:
- ✅ Interactive React frontend with routing
- ✅ Robust FastAPI backend with validation
- ✅ Real-time processing (heartbeat detection)
- ✅ Database persistence (appointments)
- ✅ Professional error handling
- ✅ Security best practices
- ✅ Scalable architecture

Perfect for a final year project presentation showcasing practical software engineering skills!

