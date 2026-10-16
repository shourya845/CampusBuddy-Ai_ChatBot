# Acceptance verification

Selected judging model: Groq openai/gpt-oss-20b.

| Criterion | Evidence |
|---|---|
| Exact CampusBuddy introduction | UI introduction, system prompt and actual live model introduction |
| Persona, scope and task rules | campusbuddy/system_prompt.txt |
| Real DB, schema and seed | SQLite; database/schema.sql; database/seed.py |
| Required seed minimums | 200 students, 25 teachers, five subjects, 20 class dates per subject, two exams |
| Six real tools | Named domain functions; live calls plus automated tests |
| Safe queries | Fixed parameterized application statements; no model SQL execution |
| Clarification | Missing-date request verified; required arguments validated |
| Confirmation | Actual proposal and explicit simulated confirmation in temporary DB; no production writes |
| Error handling | Invalid IDs, scores, ownership, DB errors and provider failures tested |
| Session memory | Live marks proposal followed by cancel it |
| Interface | Streamlit login, chat, records and confirmation tested |
| Secrets | Private .env excluded; .env.example has blank credentials |
| Submission files | README, team CampusBuddy, task T5, tools, ER diagram, requirements and ZIP |
| Actual judge replies | test_prompts.md: five live Groq replies plus blocked business rules |
| Prohibited approaches | No RAG, vector database, embeddings, fake DB tools or model-generated write SQL |

The current automated test result is recorded in docs/validation.txt. The full live workflow passed all five mandatory prompts, report-card retrieval, marks proposal, session cancellation, missing-date clarification, and blocked business-rule attempts. The live workflow used a temporary database copy and did not change the application data.

Source and test evidence support the listed technical criteria. Final judging, participant eligibility and originality assessment belong to the organizers. No bonus feature is claimed.
