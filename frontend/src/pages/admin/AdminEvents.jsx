import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { getAdminEvents, createAdminEvent, updateAdminEvent, deleteAdminEvent } from "../../services/api";
import { Calendar, Plus, Edit2, Trash2, Globe, Eye, EyeOff, X } from "lucide-react";

export default function AdminEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form toggles and states
  const [showForm, setShowForm] = useState(false);
  const [editEvent, setEditEvent] = useState(null);

  // Form fields state
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Event");
  const [description, setDescription] = useState("");
  const [venue, setVenue] = useState("");
  const [startDatetime, setStartDatetime] = useState("");
  const [endDatetime, setEndDatetime] = useState("");
  const [registrationLink, setRegistrationLink] = useState("");
  const [maxParticipants, setMaxParticipants] = useState(0);
  const [published, setPublished] = useState(false);
  const [organizer, setOrganizer] = useState("");
  const [department, setDepartment] = useState("");
  const [eligibility, setEligibility] = useState("");
  const [teamSize, setTeamSize] = useState("");
  const [prizePool, setPrizePool] = useState("");
  const [speaker, setSpeaker] = useState("");

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    setLoading(true);
    try {
      const data = await getAdminEvents();
      setEvents(data || []);
      setError(null);
    } catch (err) {
      console.error("Failed to load events:", err);
      setError("Failed to fetch events from server.");
    } finally {
      setLoading(false);
    }
  }

  // Convert ISO string (e.g. "2026-09-01T09:00:00") to input value format (e.g. "2026-09-01T09:00")
  const formatDatetimeForInput = (isoString) => {
    if (!isoString) return "";
    return isoString.substring(0, 16);
  };

  const handleOpenCreate = () => {
    setEditEvent(null);
    setTitle("");
    setCategory("Event");
    setDescription("");
    setVenue("");
    setStartDatetime("");
    setEndDatetime("");
    setRegistrationLink("");
    setMaxParticipants(0);
    setPublished(false);
    setOrganizer("");
    setDepartment("");
    setEligibility("");
    setTeamSize("");
    setPrizePool("");
    setSpeaker("");
    setShowForm(true);
  };

  const handleOpenEdit = (evt) => {
    setEditEvent(evt);
    setTitle(evt.title || "");
    setCategory(evt.category || "Event");
    setDescription(evt.description || "");
    setVenue(evt.venue || "");
    setStartDatetime(formatDatetimeForInput(evt.start_datetime));
    setEndDatetime(formatDatetimeForInput(evt.end_datetime));
    setRegistrationLink(evt.registration_link || "");
    setMaxParticipants(evt.max_participants || 0);
    setPublished(evt.published || false);
    setOrganizer(evt.organizer || "");
    setDepartment(evt.department || "");
    setEligibility(evt.eligibility || "");
    setTeamSize(evt.team_size || "");
    setPrizePool(evt.prize_pool || "");
    setSpeaker(evt.speaker || "");
    setShowForm(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      title,
      category,
      description,
      venue,
      start_datetime: startDatetime,
      end_datetime: endDatetime,
      registration_link: registrationLink || null,
      max_participants: parseInt(maxParticipants) || 0,
      published,
      organizer: organizer || null,
      department: department || null,
      eligibility: eligibility || null,
      team_size: teamSize ? parseInt(teamSize) : null,
      prize_pool: prizePool || null,
      speaker: speaker || null,
    };

    try {
      if (editEvent) {
        await updateAdminEvent(editEvent.id, payload);
        alert("Event updated successfully!");
      } else {
        await createAdminEvent(payload);
        alert("Event created successfully!");
      }
      setShowForm(false);
      loadEvents();
    } catch (err) {
      console.error("Error saving event:", err);
      alert(err.response?.data?.detail || "Failed to save event details.");
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm("Are you sure you want to delete this event? This action is irreversible.")) return;

    try {
      await deleteAdminEvent(eventId);
      alert("Event deleted successfully.");
      loadEvents();
    } catch (err) {
      console.error("Error deleting event:", err);
      alert("Failed to delete event.");
    }
  };

  const handlePublishToggle = async (evt) => {
    try {
      await updateAdminEvent(evt.id, { published: !evt.published });
      alert(`Event ${evt.published ? "unpublished" : "published"} successfully!`);
      loadEvents();
    } catch (err) {
      console.error("Error updating publish status:", err);
      alert("Failed to update status.");
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Navbar />
        <div className="flex-1 p-8 overflow-auto">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <Calendar className="text-cyan-400" />
                Events Manager
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Schedule guest lectures, tech workshops, hackathons, and announcements.
              </p>
            </div>
            <button
              onClick={handleOpenCreate}
              className="flex items-center gap-2 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-semibold transition"
            >
              <Plus size={16} />
              Create Event
            </button>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-500/50 text-red-200 p-4 rounded-xl mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Form Modal/Section */}
          {showForm && (
            <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
              <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden relative">
                <button
                  onClick={() => setShowForm(false)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
                >
                  <X size={20} />
                </button>

                <div className="p-6 border-b border-slate-805">
                  <h2 className="text-xl font-bold text-slate-100">
                    {editEvent ? "Edit Event Details" : "Create New Campus Event"}
                  </h2>
                </div>

                <form onSubmit={handleFormSubmit} className="p-6 overflow-auto space-y-4 flex-1 text-sm">
                  {/* Row 1 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1">Event Title</label>
                      <input
                        type="text"
                        required
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. Annual Tech Fest"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Category</label>
                      <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                      >
                        <option value="Event">General Event</option>
                        <option value="Hackathon">Hackathon</option>
                        <option value="Seminar">Seminar</option>
                        <option value="Workshop">Workshop</option>
                        <option value="Competition">Competition</option>
                        <option value="Guest Lecture">Guest Lecture</option>
                      </select>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-slate-400 mb-1">Description</label>
                    <textarea
                      rows="3"
                      required
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                      placeholder="Detail explanation of the event..."
                    />
                  </div>

                  {/* Row 2 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1">Venue</label>
                      <input
                        type="text"
                        required
                        value={venue}
                        onChange={(e) => setVenue(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. Seminar Hall A"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Start Date & Time</label>
                      <input
                        type="datetime-local"
                        required
                        value={startDatetime}
                        onChange={(e) => setStartDatetime(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">End Date & Time</label>
                      <input
                        type="datetime-local"
                        required
                        value={endDatetime}
                        onChange={(e) => setEndDatetime(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>

                  {/* Row 3 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1">Registration Link (Optional)</label>
                      <input
                        type="url"
                        value={registrationLink}
                        onChange={(e) => setRegistrationLink(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="https://..."
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Max Participants</label>
                      <input
                        type="number"
                        value={maxParticipants}
                        onChange={(e) => setMaxParticipants(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Speaker (Optional)</label>
                      <input
                        type="text"
                        value={speaker}
                        onChange={(e) => setSpeaker(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. Dr. John Doe"
                      />
                    </div>
                  </div>

                  {/* Row 4 */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1">Organizer</label>
                      <input
                        type="text"
                        value={organizer}
                        onChange={(e) => setOrganizer(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="Club or Office"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Department</label>
                      <input
                        type="text"
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. CSE"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Eligibility</label>
                      <input
                        type="text"
                        value={eligibility}
                        onChange={(e) => setEligibility(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. Open to All"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Team Size</label>
                      <input
                        type="number"
                        value={teamSize}
                        onChange={(e) => setTeamSize(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="Max size"
                      />
                    </div>
                  </div>

                  {/* Row 5 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1">Prize Pool</label>
                      <input
                        type="text"
                        value={prizePool}
                        onChange={(e) => setPrizePool(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-cyan-500"
                        placeholder="e.g. $1000 Cash"
                      />
                    </div>
                    <div className="flex items-center gap-2 pt-6">
                      <input
                        type="checkbox"
                        id="published"
                        checked={published}
                        onChange={(e) => setPublished(e.target.checked)}
                        className="w-4 h-4 text-cyan-600 bg-slate-950 border-slate-800 rounded focus:ring-cyan-500 focus:ring-2"
                      />
                      <label htmlFor="published" className="text-slate-300 font-semibold cursor-pointer select-none">
                        Publish Immediately
                      </label>
                    </div>
                  </div>

                  {/* Submit buttons */}
                  <div className="flex justify-end gap-3 pt-6 border-t border-slate-805">
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="px-4 py-2 border border-slate-800 rounded-lg font-semibold hover:bg-slate-800 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold transition"
                    >
                      {editEvent ? "Save Changes" : "Create Event"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Events List */}
          {loading ? (
            <div className="text-center py-20 text-slate-500">Loading events...</div>
          ) : events.length === 0 ? (
            <div className="text-center py-20 text-slate-500 border border-dashed border-slate-800 rounded-xl">
              No campus events registered yet. Click "Create Event" to schedule the first one!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map((evt) => (
                <div
                  key={evt.id}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-xs bg-slate-950 text-cyan-400 border border-slate-850 px-2 py-0.5 rounded font-mono uppercase">
                        {evt.category}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                          evt.published ? "bg-emerald-950 text-emerald-400" : "bg-slate-950 text-slate-500"
                        }`}
                      >
                        {evt.published ? "Published" : "Draft"}
                      </span>
                    </div>

                    <h2 className="text-xl font-bold text-slate-100 line-clamp-1 mb-2">{evt.title}</h2>
                    <p className="text-slate-400 text-xs line-clamp-3 leading-relaxed mb-4">
                      {evt.description}
                    </p>

                    <div className="space-y-2 bg-slate-950/65 p-3 rounded-lg text-xs text-slate-400">
                      <p>
                        📍 <strong>Venue:</strong> {evt.venue}
                      </p>
                      <p>
                        📅 <strong>Date:</strong> {evt.date || new Date(evt.start_datetime).toLocaleDateString()}
                      </p>
                      <p>
                        ⏰ <strong>Time:</strong> {evt.time || new Date(evt.start_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      {evt.speaker && (
                        <p>
                          🗣️ <strong>Speaker:</strong> {evt.speaker}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions footer */}
                  <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-805">
                    <button
                      onClick={() => handlePublishToggle(evt)}
                      className="flex items-center gap-1 text-xs font-bold text-cyan-400 hover:text-cyan-300 transition"
                      title={evt.published ? "Make Draft" : "Publish Event"}
                    >
                      {evt.published ? (
                        <>
                          <EyeOff size={14} />
                          Unpublish
                        </>
                      ) : (
                        <>
                          <Eye size={14} />
                          Publish
                        </>
                      )}
                    </button>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOpenEdit(evt)}
                        className="p-2 text-slate-400 hover:text-slate-200 border border-slate-800 hover:border-slate-700 bg-slate-950 rounded-lg transition"
                        title="Edit event"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(evt.id)}
                        className="p-2 text-red-400 hover:text-red-300 border border-slate-800 hover:border-slate-700 bg-slate-950 rounded-lg transition"
                        title="Delete event"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
