import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Report() {
  const [report, setReport] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState("");

  const loadReport = async () => {
    const data = await api("/reports/me");
    setReport(data);
  };

  useEffect(() => {
    loadReport();
  }, []);

  const handleDelete = async () => {
    const confirmed = window.confirm(
      "Are you sure? This will permanently delete your diagnostic data for this organization."
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);
      setMessage("");

      await api("/reports/me", {
        method: "DELETE",
      });

      await loadReport();

      setMessage("Your diagnostic data was deleted successfully.");
    } catch (error) {
      setMessage(error.message || "Unable to delete your diagnostic data.");
    } finally {
      setDeleting(false);
    }
  };

  if (!report) return <p>Loading…</p>;

  return (
    <div className="card">
      <h2>
        {report.name}: {report.level}
      </h2>

      <p>Average score: {report.average_score}</p>

      <h3>Risks</h3>
      <ul>
        {report.risks.length === 0 ? (
          <li>No risks recorded</li>
        ) : (
          report.risks.map((r) => <li key={r}>{r}</li>)
        )}
      </ul>

      <h3>Next steps</h3>
      <ul>
        {report.next_steps.map((s) => <li key={s}>{s}</li>)}
      </ul>

      {message && <p>{message}</p>}

      <button onClick={handleDelete} disabled={deleting}>
        {deleting ? "Deleting..." : "Delete my diagnostic data"}
      </button>
    </div>
  );
}