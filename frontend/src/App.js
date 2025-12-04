import React, { useState } from "react";

function App() {
  const [cv, setCv] = useState(null);
  const [jobUrl, setJobUrl] = useState("");
  const [analysis, setAnalysis] = useState(null);

  const [projects, setProjects] = useState([""]);
  const [interview, setInterview] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);

  const [hasStarted, setHasStarted] = useState(false);

  const api = process.env.REACT_APP_API_URL;

  /** ------------------------------
   *  ANALYZE
   * ------------------------------ */
  const handleAnalyze = async () => {
    if (!cv || !jobUrl) return;

    const form = new FormData();
    form.append("cv", cv);
    form.append("jobUrl", jobUrl);

    try {
      const res = await fetch(`${api}/analyze`, {
        method: "POST",
        body: form,
      });

      const data = await res.json();

      setAnalysis({
        matchScore: data.matchScore ?? 0,
        skillsMatch: data.skillsMatch ?? [],
        missingSkills: data.missingSkills ?? [],
      });

      setInterview(null);
      setUserAnswers([]);
    } catch (err) {
      console.log("Analyze error:", err);
    }
  };

  /** ------------------------------
   *  INTERVIEW GENERATION
   * ------------------------------ */
  const handleInterview = async () => {
    if (!analysis) return;

    const nonEmptyProjects = projects.filter((p) => p.trim() !== "");
    if (nonEmptyProjects.length === 0) return;

    const form = new FormData();
    form.append("cv", cv);
    form.append("jobUrl", jobUrl);
    form.append("projects", JSON.stringify(nonEmptyProjects));

    form.append("missingSkills", JSON.stringify(analysis.missingSkills));
    form.append("skillsMatch", JSON.stringify(analysis.skillsMatch));
    form.append("matchScore", analysis.matchScore);

    try {
      const res = await fetch(`${api}/interview`, {
        method: "POST",
        body: form,
      });

      const data = await res.json();

      setInterview(data);
      setUserAnswers((data.questions || []).map(() => ""));
    } catch (err) {
      console.log("Interview error:", err);
    }
  };

  /** ------------------------------ */
  const updateProject = (idx, value) => {
    const updated = [...projects];
    updated[idx] = value;
    setProjects(updated);
  };

  const addProject = () => setProjects([...projects, ""]);

  const removeProject = (idx) => {
    if (projects.length === 1) return;
    setProjects(projects.filter((_, i) => i !== idx));
  };

  const updateUserAnswer = (index, text) => {
    const updated = [...userAnswers];
    updated[index] = text;
    setUserAnswers(updated);
  };

  const handleReset = () => {
    setAnalysis(null);
    setInterview(null);
    setProjects([""]);
    setUserAnswers([]);
    setCv(null);
    setJobUrl("");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg,#1e1b4b,#0f172a)",
        color: "white",
        fontFamily: "Inter, system-ui",
        paddingBottom: "6rem",
      }}
    >
      <div style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}>
        {/* HEADER */}
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "2rem",
          }}
        >
          <h1 style={{ margin: 0 }}>JobbTren</h1>

          {hasStarted && (analysis || interview) && (
            <button
              onClick={handleReset}
              style={{
                background: "#f87171",
                border: "none",
                padding: "8px 14px",
                borderRadius: "999px",
                cursor: "pointer",
                color: "white",
              }}
            >
              Ny analyse
            </button>
          )}
        </header>

        {/* LANDING KNAPP */}
        {!hasStarted && (
          <div style={{ textAlign: "center", paddingTop: "4rem" }}>
            <button
              onClick={() => setHasStarted(true)}
              style={{
                width: "140px",
                height: "140px",
                borderRadius: "50%",
                fontSize: "1.1rem",
                fontWeight: "bold",
                background: "linear-gradient(135deg,#a855f7,#ec4899)",
                border: "none",
                color: "white",
                cursor: "pointer",
              }}
            >
              Start analyse
            </button>
          </div>
        )}

        {/* INPUT FORM */}
        {hasStarted && (
          <section
            style={{
              background: "rgba(255,255,255,0.1)",
              padding: "1.5rem",
              borderRadius: "16px",
              marginBottom: "1.5rem",
            }}
          >
            <h2>Steg 1: CV og stilling</h2>

            <label>Last opp CV (PDF)</label>
            <input
              type="file"
              onChange={(e) => setCv(e.target.files[0] || null)}
            />

            <label style={{ marginTop: "1rem", display: "block" }}>
              Stillingslink
            </label>
            <input
              type="text"
              placeholder="https://finn.no/..."
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "10px",
                marginTop: "4px",
              }}
            />

            <button
              onClick={handleAnalyze}
              disabled={!cv || !jobUrl}
              style={{
                marginTop: "1rem",
                padding: "10px 18px",
                borderRadius: "999px",
                background:
                  !cv || !jobUrl
                    ? "gray"
                    : "linear-gradient(135deg,#6366f1,#4f46e5)",
                border: "none",
                cursor: "pointer",
                color: "white",
              }}
            >
              Analyser CV
            </button>
          </section>
        )}

        {/* ANALYSE RESULTAT */}
        {hasStarted && analysis && (
          <>
            <section
              style={{
                background: "rgba(255,255,255,0.1)",
                padding: "1.5rem",
                borderRadius: "16px",
                marginBottom: "1.5rem",
              }}
            >
              <h2>Match: {analysis.matchScore}%</h2>

              <h3>Matchende skills</h3>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {analysis.skillsMatch.length > 0 ? (
                  analysis.skillsMatch.map((s) => (
                    <span
                      key={s}
                      style={{
                        background: "rgba(34,197,94,0.3)",
                        padding: "4px 8px",
                        borderRadius: "999px",
                      }}
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span>Ingen treff</span>
                )}
              </div>

              <h3 style={{ marginTop: "1rem" }}>Manglende skills</h3>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {analysis.missingSkills.length > 0 ? (
                  analysis.missingSkills.map((s) => (
                    <span
                      key={s}
                      style={{
                        background: "rgba(239,68,68,0.3)",
                        padding: "4px 8px",
                        borderRadius: "999px",
                      }}
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span>Ingen mangler</span>
                )}
              </div>
            </section>

            {/* PROSJEKT INPUT */}
            <section
              style={{
                background: "rgba(255,255,255,0.1)",
                padding: "1.5rem",
                borderRadius: "16px",
                marginBottom: "1.5rem",
              }}
            >
              <h2>Steg 3: Prosjekter</h2>

              {projects.map((p, idx) => (
                <div key={idx} style={{ marginBottom: "1rem" }}>
                  <textarea
                    placeholder="Beskriv prosjektet..."
                    value={p}
                    onChange={(e) => updateProject(idx, e.target.value)}
                    style={{
                      width: "100%",
                      minHeight: "100px",
                      borderRadius: "10px",
                      padding: "10px",
                    }}
                  />

                  {projects.length > 1 && (
                    <button
                      onClick={() => removeProject(idx)}
                      style={{
                        background: "#dc2626",
                        color: "white",
                        border: "none",
                        padding: "4px 10px",
                        borderRadius: "10px",
                        cursor: "pointer",
                        marginTop: "4px",
                      }}
                    >
                      Fjern prosjekt
                    </button>
                  )}
                </div>
              ))}

              <button
                onClick={addProject}
                style={{
                  background: "#16a34a",
                  padding: "6px 12px",
                  borderRadius: "999px",
                  border: "none",
                  color: "white",
                  cursor: "pointer",
                  marginRight: "8px",
                }}
              >
                + Legg til prosjekt
              </button>

              <button
                onClick={handleInterview}
                style={{
                  background: "linear-gradient(135deg,#f97316,#ea580c)",
                  padding: "8px 14px",
                  borderRadius: "999px",
                  border: "none",
                  cursor: "pointer",
                  color: "white",
                }}
              >
                Tren til intervju
              </button>
            </section>
          </>
        )}

        {/* INTERVJU */}
        {hasStarted && interview && (
          <section
            style={{
              background: "rgba(255,255,255,0.1)",
              padding: "1.5rem",
              borderRadius: "16px",
            }}
          >
            <h2>Intervjutrening</h2>

            {interview.questions?.map((q, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: "1.5rem",
                  background: "rgba(255,255,255,0.05)",
                  padding: "1rem",
                  borderRadius: "12px",
                }}
              >
                <strong>{q}</strong>

                <div
                  style={{
                    background: "rgba(99,102,241,0.3)",
                    padding: "0.75rem",
                    borderRadius: "8px",
                    marginTop: "0.5rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  {interview.answers?.[idx]}
                </div>

                <textarea
                  value={userAnswers[idx] || ""}
                  onChange={(e) => updateUserAnswer(idx, e.target.value)}
                  placeholder="Hvordan ville du svart?"
                  style={{
                    width: "100%",
                    minHeight: "80px",
                    borderRadius: "10px",
                    padding: "10px",
                  }}
                />
              </div>
            ))}
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
