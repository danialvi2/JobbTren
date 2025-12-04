import React, { useState } from "react";

function App() {
  const [cv, setCv] = useState(null);
  const [jobUrl, setJobUrl] = useState("");
  const [analysis, setAnalysis] = useState(null);

  const [projects, setProjects] = useState([""]);
  const [interview, setInterview] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);

  // UI-flow: har brukeren startet prosessen?
  const [hasStarted, setHasStarted] = useState(false);

  const api = process.env.REACT_APP_API_URL;

  // --- analyze request ---
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

      // ny analyse nuller tidligere intervju
      setAnalysis(data);
      setInterview(null);
      setUserAnswers([]);
    } catch (err) {
      console.log("Analyze error:", err);
    }
  };

  // --- interview request ---
  const handleInterview = async () => {
    if (!analysis) return;

    const nonEmptyProjects = projects.filter(
      (p) => p.trim() !== ""
    );
    if (nonEmptyProjects.length === 0) return;

    const form = new FormData();
    form.append("cv", cv);
    form.append("jobUrl", jobUrl);
    form.append("projects", JSON.stringify(projects));

    // sender analyze-resultater videre til backend
    form.append(
      "missingSkills",
      JSON.stringify(analysis.missingSkills)
    );
    form.append(
      "skillsMatch",
      JSON.stringify(analysis.skillsMatch)
    );
    form.append("matchScore", analysis.matchScore);

    try {
      const res = await fetch(`${api}/interview`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();

      setInterview(data);
      setUserAnswers(
        (data.questions || []).map(() => "")
      );
    } catch (err) {
      console.log("Interview error:", err);
    }
  };

  // prosjekt-editor
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

  // brukerens egne intervjusvar
  const updateUserAnswer = (index, text) => {
    const updated = [...userAnswers];
    updated[index] = text;
    setUserAnswers(updated);
  };

  const handleStart = () => {
    setHasStarted(true);
  };

  const handleReset = () => {
    setAnalysis(null);
    setInterview(null);
    setProjects([""]);
    setUserAnswers([]);
    setCv(null);
    setJobUrl("");
  };

  // --- UI ---
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f5f7",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "960px",
          margin: "0 auto",
          padding: "2.5rem 1.5rem 3rem",
        }}
      >
        {/* Header */}
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
                padding: "8px 14px",
                borderRadius: "999px",
                border: "1px solid #ddd",
                background: "#fff",
                cursor: "pointer",
                fontSize: "0.9rem",
              }}
            >
              Reset til ny stilling
            </button>
          )}
        </header>

        {/* SCENE 1 – Landing med rund knapp */}
        {!hasStarted && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "4rem 1rem 5rem",
              textAlign: "center",
            }}
          >
            <p
              style={{
                maxWidth: "420px",
                marginBottom: "2rem",
                color: "#555",
              }}
            >
              Tren på ekte intervjusituasjoner basert på din CV og en
              konkret stillingsannonse. Trykk under for å starte.
            </p>

            <button
              onClick={handleStart}
              style={{
                width: "140px",
                height: "140px",
                borderRadius: "50%",
                border: "none",
                background:
                  "linear-gradient(135deg, #ffb347, #ff7b54)",
                color: "#fff",
                fontSize: "1.1rem",
                fontWeight: 600,
                cursor: "pointer",
                boxShadow:
                  "0 10px 25px rgba(0,0,0,0.15)",
              }}
            >
              Start analyse
            </button>
          </div>
        )}

        {/* SCENE 2+ – CV + URL + Analyze alltid synlig etter start */}
        {hasStarted && (
          <section
            style={{
              background: "#ffffff",
              borderRadius: "18px",
              padding: "1.5rem 1.5rem 1.75rem",
              boxShadow:
                "0 10px 25px rgba(15, 23, 42, 0.06)",
              marginBottom: "1.75rem",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: "0.75rem",
                fontSize: "1.15rem",
              }}
            >
              Steg 1: CV og stilling
            </h2>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                marginTop: "0.5rem",
              }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.9rem",
                    marginBottom: "0.25rem",
                  }}
                >
                  Last opp CV (PDF)
                </label>
                <input
                  type="file"
                  onChange={(e) =>
                    setCv(e.target.files[0] || null)
                  }
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "0.9rem",
                    marginBottom: "0.25rem",
                  }}
                >
                  Lim inn lenke til stillingsannonsen
                </label>
                <input
                  type="text"
                  placeholder="https://www.finn.no/job/..."
                  value={jobUrl}
                  onChange={(e) =>
                    setJobUrl(e.target.value)
                  }
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "10px",
                    border: "1px solid #d0d0d5",
                    fontSize: "0.95rem",
                  }}
                />
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "0.75rem",
                  marginTop: "0.5rem",
                }}
              >
                <button
                  onClick={handleAnalyze}
                  disabled={!cv || !jobUrl}
                  style={{
                    padding: "10px 18px",
                    borderRadius: "999px",
                    border: "none",
                    fontSize: "0.95rem",
                    fontWeight: 500,
                    cursor:
                      !cv || !jobUrl
                        ? "not-allowed"
                        : "pointer",
                    background:
                      !cv || !jobUrl
                        ? "#d4d4d8"
                        : "linear-gradient(135deg,#2563eb,#1d4ed8)",
                    color: "#fff",
                  }}
                >
                  Analyser CV mot stillingen
                </button>
              </div>
            </div>
          </section>
        )}

        {/* SCENE 3 – Analyse resultat */}
        {hasStarted && analysis && (
          <section
            style={{
              background: "#ffffff",
              borderRadius: "18px",
              padding: "1.5rem 1.75rem 1.5rem",
              boxShadow:
                "0 10px 25px rgba(15, 23, 42, 0.06)",
              marginBottom: "1.75rem",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: "0.5rem",
                fontSize: "1.15rem",
              }}
            >
              Steg 2: Analyse resultat
            </h2>

            <p
              style={{
                marginTop: 0,
                marginBottom: "0.75rem",
              }}
            >
              <strong>Jobbmatch:</strong>{" "}
              {analysis.matchScore}%
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "1rem",
              }}
            >
              <div>
                <h3
                  style={{
                    marginBottom: "0.4rem",
                    fontSize: "0.98rem",
                  }}
                >
                  Matchende styrker
                </h3>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.35rem",
                  }}
                >
                  {analysis.skillsMatch?.map((s) => (
                    <span
                      key={s}
                      style={{
                        padding:
                          "4px 8px",
                        borderRadius:
                          "999px",
                        background:
                          "#e0f2fe",
                        fontSize:
                          "0.85rem",
                      }}
                    >
                      {s}
                    </span>
                  ))}
                  {(!analysis.skillsMatch ||
                    analysis.skillsMatch
                      .length === 0) && (
                    <span
                      style={{
                        fontSize:
                          "0.85rem",
                        color: "#6b7280",
                      }}
                    >
                      Ingen matchede
                      skills funnet.
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h3
                  style={{
                    marginBottom: "0.4rem",
                    fontSize: "0.98rem",
                  }}
                >
                  Manglende skills
                </h3>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.35rem",
                  }}
                >
                  {analysis.missingSkills?.map(
                    (s) => (
                      <span
                        key={s}
                        style={{
                          padding:
                            "4px 8px",
                          borderRadius:
                            "999px",
                          background:
                            "#fee2e2",
                          fontSize:
                            "0.85rem",
                        }}
                      >
                        {s}
                      </span>
                    )
                  )}
                  {(!analysis.missingSkills ||
                    analysis.missingSkills
                      .length === 0) && (
                    <span
                      style={{
                        fontSize:
                          "0.85rem",
                        color: "#6b7280",
                      }}
                    >
                      Ingen tydelige hull
                      i kravene.
                    </span>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* SCENE 3.5 – Prosjekt-input (etter analyse) */}
        {hasStarted && analysis && (
          <section
            style={{
              background: "#ffffff",
              borderRadius: "18px",
              padding: "1.5rem 1.75rem 1.75rem",
              boxShadow:
                "0 10px 25px rgba(15, 23, 42, 0.06)",
              marginBottom: "1.75rem",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: "0.5rem",
                fontSize: "1.15rem",
              }}
            >
              Steg 3: Prosjekter
            </h2>

            <p
              style={{
                fontSize: "0.92rem",
                color: "#4b5563",
                marginTop: 0,
                marginBottom: "0.75rem",
              }}
            >
              Skriv én eller flere prosjekter du har jobbet
              med. JobbTren bruker disse for å bygge
              konkrete intervjuhistorier.
            </p>

            {projects.map((p, idx) => (
              <div
                key={idx}
                style={{ marginBottom: "1rem" }}
              >
                <textarea
                  placeholder="Beskriv et prosjekt du har jobbet med..."
                  value={p}
                  onChange={(e) =>
                    updateProject(
                      idx,
                      e.target.value
                    )
                  }
                  style={{
                    width: "100%",
                    minHeight: "110px",
                    borderRadius: "10px",
                    border: "1px solid #d4d4d8",
                    padding: "10px 12px",
                    fontSize: "0.95rem",
                  }}
                />
                {projects.length > 1 && (
                  <button
                    onClick={() =>
                      removeProject(idx)
                    }
                    style={{
                      marginTop: "5px",
                      background: "#fee2e2",
                      color: "#b91c1c",
                      padding:
                        "5px 10px",
                      borderRadius:
                        "999px",
                      border: "none",
                      cursor: "pointer",
                      fontSize:
                        "0.8rem",
                    }}
                  >
                    Slett prosjekt
                  </button>
                )}
              </div>
            ))}

            <div
              style={{
                display: "flex",
                gap: "0.75rem",
                alignItems: "center",
                marginTop: "0.5rem",
              }}
            >
              <button
                onClick={addProject}
                style={{
                  background: "#16a34a",
                  color: "#fff",
                  padding: "8px 12px",
                  borderRadius: "999px",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                + Legg til prosjekt
              </button>

              <button
                onClick={handleInterview}
                style={{
                  padding: "9px 16px",
                  borderRadius: "999px",
                  border: "none",
                  background:
                    "linear-gradient(135deg,#f97316,#ea580c)",
                  color: "#fff",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Tren til intervju
              </button>
            </div>
          </section>
        )}

        {/* SCENE 4 – Intervjutrening */}
        {hasStarted && interview && (
          <section
            style={{
              background: "#ffffff",
              borderRadius: "18px",
              padding: "1.5rem 1.75rem 2rem",
              boxShadow:
                "0 10px 25px rgba(15, 23, 42, 0.06)",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: "1rem",
                fontSize: "1.15rem",
              }}
            >
              Steg 4: Intervjutrening
            </h2>

            {(interview.questions || []).map(
              (q, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: "1.75rem",
                    padding: "1rem 1rem 1.1rem",
                    borderRadius: "16px",
                    border:
                      "1px solid #e5e7eb",
                    background: "#fafafa",
                  }}
                >
                  <p
                    style={{
                      marginTop: 0,
                      marginBottom: "0.5rem",
                    }}
                  >
                    <strong>{q}</strong>
                  </p>

                  <div
                    style={{
                      background: "#eff6ff",
                      padding: "0.75rem 0.8rem",
                      borderRadius: "10px",
                      fontSize: "0.92rem",
                      marginBottom: "0.8rem",
                      borderLeft:
                        "4px solid #2563eb",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        marginBottom: "0.25rem",
                        textTransform:
                          "uppercase",
                        letterSpacing:
                          "0.04em",
                        color: "#1d4ed8",
                      }}
                    >
                      Coachingsvar
                    </div>
                    {interview.answers?.[idx]}
                  </div>

                  <textarea
                    placeholder="Hvordan ville du svart på dette intervjuet?"
                    value={userAnswers[idx] || ""}
                    onChange={(e) =>
                      updateUserAnswer(
                        idx,
                        e.target.value
                      )
                    }
                    style={{
                      width: "100%",
                      minHeight: "80px",
                      borderRadius: "10px",
                      border: "1px solid #d4d4d8",
                      padding: "9px 11px",
                      fontSize: "0.95rem",
                    }}
                  />
                </div>
              )
            )}
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
