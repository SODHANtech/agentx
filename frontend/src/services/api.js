import axios from "axios";

// Match localhost backend address
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach JWT token from localStorage to every request automatically
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Catch expired or invalid token errors (401 Unauthorized) globally
API.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// =======================
// Authentication
// =======================

export const login = async (email, password) => {
  try {
    const response = await API.post("/auth/login", { email, password });
    if (response.data?.access_token) {
      localStorage.setItem("access_token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
    }
    return response.data;
  } catch (error) {
    console.error("Login failed:", error);
    throw error;
  }
};

export const register = async (name, email, password, role = "Student", cgpa = 8.2, backlogs = 0) => {
  try {
    const response = await API.post("/auth/register", {
      name,
      email,
      password,
      role,
      cgpa,
      backlogs
    });
    return response.data;
  } catch (error) {
    console.error("Registration failed:", error);
    throw error;
  }
};

export const getMe = async () => {
  try {
    const response = await API.get("/auth/me");
    return response.data;
  } catch (error) {
    console.error("Fetch profile failed:", error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
};

// =======================
// AI Chat
// =======================

export const askAI = async (query) => {
  try {
    const response = await API.get("/ask", {
      params: { query },
    });
    return response.data;
  } catch (error) {
    console.error("Error calling /ask:", error);
    throw error;
  }
};

// =======================
// Events
// =======================

export const getEvents = async () => {
  try {
    const response = await API.get("/events");
    return response.data;
  } catch (error) {
    console.error("Error fetching events:", error);
    throw error;
  }
};

export const registerEvent = async (eventTitle) => {
  try {
    const response = await API.post("/events/register", {
      event: eventTitle,
    });
    return response.data;
  } catch (error) {
    console.error("Error registering event:", error);
    throw error;
  }
};

export const cancelEvent = async (eventTitle) => {
  try {
    const response = await API.post("/events/cancel", {
      event: eventTitle,
    });
    return response.data;
  } catch (error) {
    console.error("Error cancelling event:", error);
    throw error;
  }
};

export const getRegisteredEvents = async () => {
  try {
    const response = await API.get("/events/registrations");
    return response.data;
  } catch (error) {
    console.error("Error fetching registered events:", error);
    throw error;
  }
};

export const getAdminEvents = async () => {
  try {
    const response = await API.get("/admin/events");
    return response.data;
  } catch (error) {
    console.error("Error fetching admin events:", error);
    throw error;
  }
};

export const createAdminEvent = async (eventData) => {
  try {
    const response = await API.post("/admin/events", eventData);
    return response.data;
  } catch (error) {
    console.error("Error creating admin event:", error);
    throw error;
  }
};

export const updateAdminEvent = async (eventId, eventData) => {
  try {
    const response = await API.put(`/admin/events/${eventId}`, eventData);
    return response.data;
  } catch (error) {
    console.error("Error updating admin event:", error);
    throw error;
  }
};

export const deleteAdminEvent = async (eventId) => {
  try {
    const response = await API.delete(`/admin/events/${eventId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting admin event:", error);
    throw error;
  }
};

// =======================
// Dashboard & Other
// =======================

export const getDashboard = async () => {
  try {
    const response = await API.get("/dashboard");
    return response.data;
  } catch (error) {
    console.error("Error fetching dashboard:", error);
    throw error;
  }
};

export const getNotifications = async () => {
  try {
    const response = await API.get("/notifications");
    return response.data;
  } catch (error) {
    console.error("Error fetching notifications:", error);
    throw error;
  }
};

export const analyzeResume = async (file) => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await API.post("/resume/analyze", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error analyzing resume:", error);
    throw error;
  }
};

// =======================
// Student Services
// =======================

export const getAllServices = async () => {
  try {
    const response = await API.get("/student-services");
    return response.data;
  } catch (error) {
    console.error("Error fetching student services:", error);
    throw error;
  }
};

export const getHostelInfo = async () => {
  try {
    const response = await API.get("/student-services/hostel");
    return response.data;
  } catch (error) {
    console.error("Error fetching hostel info:", error);
    throw error;
  }
};

export const getLibraryInfo = async () => {
  try {
    const response = await API.get("/student-services/library");
    return response.data;
  } catch (error) {
    console.error("Error fetching library info:", error);
    throw error;
  }
};

export const getScholarships = async () => {
  try {
    const response = await API.get("/student-services/scholarships");
    return response.data;
  } catch (error) {
    console.error("Error fetching scholarships:", error);
    throw error;
  }
};

export const getTransport = async () => {
  try {
    const response = await API.get("/student-services/transport");
    return response.data;
  } catch (error) {
    console.error("Error fetching transport info:", error);
    throw error;
  }
};

export const submitGrievance = async (category, description) => {
  try {
    const response = await API.post("/student-services/grievance", {
      category,
      description,
    });
    return response.data;
  } catch (error) {
    console.error("Error submitting grievance:", error);
    throw error;
  }
};

export const getStudentRequests = async () => {
  try {
    const response = await API.get("/student/requests");
    return response.data;
  } catch (error) {
    console.error("Error fetching student requests:", error);
    throw error;
  }
};

export const createStudentRequest = async (requestData) => {
  try {
    const response = await API.post("/student/requests", requestData);
    return response.data;
  } catch (error) {
    console.error("Error creating student request:", error);
    throw error;
  }
};

export const getStudentRequestHistory = async (requestId) => {
  try {
    const response = await API.get(`/student/requests/${requestId}/history`);
    return response.data;
  } catch (error) {
    console.error("Error fetching request history:", error);
    throw error;
  }
};

export const getAdminRequests = async () => {
  try {
    const response = await API.get("/admin/requests");
    return response.data;
  } catch (error) {
    console.error("Error fetching admin requests:", error);
    throw error;
  }
};

export const getAdminRequestById = async (requestId) => {
  try {
    const response = await API.get(`/admin/requests/${requestId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching admin request by ID:", error);
    throw error;
  }
};

export const updateAdminRequest = async (requestId, requestData) => {
  try {
    const response = await API.put(`/admin/requests/${requestId}`, requestData);
    return response.data;
  } catch (error) {
    console.error("Error updating admin request:", error);
    throw error;
  }
};

// =======================
// Communications & Scheduling
// =======================

export const getAnnouncements = async () => {
  try {
    const response = await API.get("/communications");
    return response.data;
  } catch (error) {
    console.error("Error fetching announcements:", error);
    throw error;
  }
};

export const draftEmail = async (recipient, subject, purpose) => {
  try {
    const response = await API.post("/communications/draft-email", {
      recipient,
      subject,
      purpose,
    });
    return response.data;
  } catch (error) {
    console.error("Error drafting email:", error);
    throw error;
  }
};

export const sendNotification = async (title, message, audience) => {
  try {
    const response = await API.post("/communications/notify", {
      title,
      message,
      audience,
    });
    return response.data;
  } catch (error) {
    console.error("Error sending notification:", error);
    throw error;
  }
};

export const createAnnouncement = async (title, content, category) => {
  try {
    const response = await API.post("/communications/announcement", {
      title,
      content,
      category,
    });
    return response.data;
  } catch (error) {
    console.error("Error creating announcement:", error);
    throw error;
  }
};

export const bookAppointment = async (officer, date, timeSlot, reason) => {
  try {
    const response = await API.post("/communications/schedule-appointment", {
      officer,
      date,
      time_slot: timeSlot,
      reason,
    });
    return response.data;
  } catch (error) {
    console.error("Error booking appointment:", error);
    throw error;
  }
};

// =======================
// Admin AI Complaint Intelligence
// =======================

export const triggerClustering = async () => {
  try {
    const response = await API.post("/admin/complaints/cluster");
    return response.data;
  } catch (error) {
    console.error("Error triggering semantic clustering:", error);
    throw error;
  }
};

export const getClusters = async () => {
  try {
    const response = await API.get("/admin/clusters");
    return response.data;
  } catch (error) {
    console.error("Error fetching systemic clusters:", error);
    throw error;
  }
};

export const broadcastResolution = async (clusterId) => {
  try {
    const response = await API.post(`/admin/clusters/${clusterId}/broadcast`);
    return response.data;
  } catch (error) {
    console.error("Error broadcasting resolution:", error);
    throw error;
  }
};

export const getHealth = async () => {
  try {
    const response = await API.get("/health");
    return response.data;
  } catch (error) {
    console.error("Error fetching health stats:", error);
    throw error;
  }
};