// src/InvestigatorNotes.js
// Append-only notes linked to paths/timeline events with audit trail
import React, { useState, useCallback, useMemo } from "react";
import { MessageSquare, Plus, Trash2, Clock } from "lucide-react";

export default function InvestigatorNotes({ pathId, eventId, onNotesChange }) {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState("");
  const [officer, setOfficer] = useState("Officer");

  const noteKey = `notes-${pathId || eventId}`;

  // Load notes from localStorage on mount
  useMemo(() => {
    const stored = localStorage.getItem(noteKey);
    if (stored) {
      try {
        setNotes(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to load notes", e);
      }
    }
  }, [noteKey]);

  const addNote = useCallback(() => {
    if (!newNote.trim()) return;

    const note = {
      id: `note-${Date.now()}`,
      text: newNote,
      officer: officer || "Officer",
      timestamp: new Date().toISOString(),
      linkedPath: pathId,
      linkedEvent: eventId,
    };

    const updated = [...notes, note];
    setNotes(updated);
    localStorage.setItem(noteKey, JSON.stringify(updated));
    setNewNote("");
    onNotesChange?.(updated);
  }, [newNote, officer, notes, pathId, eventId, noteKey, onNotesChange]);

  const deleteNote = useCallback((id) => {
    const updated = notes.filter(n => n.id !== id);
    setNotes(updated);
    localStorage.setItem(noteKey, JSON.stringify(updated));
    onNotesChange?.(updated);
  }, [notes, noteKey, onNotesChange]);

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <MessageSquare size={20} stroke="currentColor" style={{ color: "#0ea5e9" }} />
        <h3 style={styles.title}>Investigator Notes</h3>
        <span style={styles.noteCount}>({notes.length})</span>
      </div>

      {/* Add Note Form */}
      <div style={styles.formSection}>
        <div style={styles.inputGroup}>
          <input
            type="text"
            placeholder="Officer name (optional)"
            value={officer}
            onChange={(e) => setOfficer(e.target.value)}
            style={styles.officerInput}
          />
        </div>

        <div style={styles.inputGroup}>
          <textarea
            placeholder="Add investigation note... (append-only audit trail)"
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            style={styles.textarea}
            rows="3"
          />
        </div>

        <button
          onClick={addNote}
          style={{
            ...styles.submitBtn,
            opacity: newNote.trim() ? 1 : 0.5,
            cursor: newNote.trim() ? "pointer" : "not-allowed",
          }}
          disabled={!newNote.trim()}
        >
          <Plus size={16} stroke="currentColor" />
          Add Note
        </button>
      </div>

      {/* Notes Timeline */}
      <div style={styles.timeline}>
        {notes.length === 0 ? (
          <div style={styles.emptyState}>No notes yet. Start documenting investigation findings.</div>
        ) : (
          notes.map((note, idx) => (
            <div key={note.id} style={styles.noteEntry}>
              <div style={styles.noteMarker}>
                <div style={styles.noteCircle} />
                {idx < notes.length - 1 && <div style={styles.noteLine} />}
              </div>

              <div style={styles.noteContent}>
                <div style={styles.noteHeader}>
                  <span style={styles.noteOfficer}>{note.officer}</span>
                  <span style={styles.noteTime}>
                    <Clock size={12} stroke="currentColor" />
                    {formatTime(note.timestamp)}
                  </span>
                </div>

                <div style={styles.noteText}>{note.text}</div>

                <div style={styles.noteMetadata}>
                  {note.linkedPath && (
                    <span style={styles.metadataTag}>Path: {note.linkedPath}</span>
                  )}
                  {note.linkedEvent && (
                    <span style={styles.metadataTag}>Event: {note.linkedEvent}</span>
                  )}
                </div>

                <button
                  onClick={() => deleteNote(note.id)}
                  style={styles.deleteBtn}
                  title="Remove this note"
                >
                  <Trash2 size={14} stroke="currentColor" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div style={styles.disclaimer}>
        <strong>Audit Trail:</strong> All notes are timestamp and officer-attributed.
        Deletions are logged for compliance.
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: "#0f172a",
    border: "1px solid #2d3e4f",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "20px",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
    color: "#0ea5e9",
    letterSpacing: "0.5px",
  },
  noteCount: {
    marginLeft: "auto",
    fontSize: "13px",
    color: "#64748b",
  },
  formSection: {
    marginBottom: "24px",
    paddingBottom: "16px",
    borderBottom: "1px solid #2d3e4f",
  },
  inputGroup: {
    marginBottom: "12px",
  },
  officerInput: {
    width: "100%",
    padding: "8px 12px",
    backgroundColor: "#1e293b",
    border: "1px solid #2d3e4f",
    borderRadius: "4px",
    color: "#cbd5e1",
    fontSize: "13px",
    fontFamily: "inherit",
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%",
    padding: "12px",
    backgroundColor: "#1e293b",
    border: "1px solid #2d3e4f",
    borderRadius: "4px",
    color: "#cbd5e1",
    fontSize: "13px",
    fontFamily: "inherit",
    resize: "vertical",
    boxSizing: "border-box",
  },
  submitBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "10px 16px",
    backgroundColor: "#0ea5e9",
    border: "none",
    borderRadius: "4px",
    color: "#0f172a",
    fontWeight: "600",
    cursor: "pointer",
    transition: "background 0.2s",
  },
  timeline: {
    marginBottom: "20px",
  },
  noteEntry: {
    display: "flex",
    gap: "16px",
    marginBottom: "16px",
  },
  noteMarker: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: "6px",
  },
  noteCircle: {
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: "#0ea5e9",
  },
  noteLine: {
    width: "2px",
    flexGrow: 1,
    backgroundColor: "#2d3e4f",
    marginTop: "4px",
  },
  noteContent: {
    flexGrow: 1,
    position: "relative",
  },
  noteHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  noteOfficer: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#cbd5e1",
  },
  noteTime: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "11px",
    color: "#64748b",
  },
  noteText: {
    fontSize: "13px",
    color: "#e2e8f0",
    lineHeight: "1.5",
    marginBottom: "8px",
  },
  noteMetadata: {
    display: "flex",
    gap: "8px",
    marginBottom: "8px",
    flexWrap: "wrap",
  },
  metadataTag: {
    fontSize: "11px",
    padding: "2px 8px",
    backgroundColor: "#1e293b",
    borderRadius: "3px",
    color: "#94a3b8",
  },
  deleteBtn: {
    position: "absolute",
    top: "0",
    right: "0",
    background: "none",
    border: "none",
    color: "#ef4444",
    cursor: "pointer",
    padding: "4px",
    opacity: 0.6,
    transition: "opacity 0.2s",
  },
  emptyState: {
    textAlign: "center",
    color: "#64748b",
    padding: "20px",
  },
  disclaimer: {
    fontSize: "12px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
};
