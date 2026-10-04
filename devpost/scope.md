---
doc: scope
status: approved
---

# Course-Grounded Study Partner

A focused study app that turns a student's own course material into active practice and evidence-based feedback.

## The Unique Kernel
The student's material is the sole source for both the practice question and the feedback. The question and evaluation must be based only on the material the student supplies, without web searches or unrelated general knowledge. Feedback points to supporting evidence in that material; if a claim cannot be supported by it, the app must not present it as evidence from the material.

## Who It's For
A university student preparing for a test or exam who has lecture notes or other course material but struggles to turn it into useful practice questions. Today, they may reread notes or ask a general AI chatbot that can answer from broad knowledge instead of their specific course content.

## The Core Loop
The student pastes a short excerpt of course material, chooses a topic, and gets one focused practice question. They answer in their own words, then review feedback explaining what they got right, what they missed, and the evidence in their material. They can continue with another question.

## Inspiration & Identity
A focused study partner that makes studying active. It tests understanding rather than acting as a general-purpose chatbot. No specific visual references or aesthetic direction have been chosen.

## Why This Matters to the Learner
The learner wants to make studying more active, help students identify gaps in their understanding, and build a useful, distinctive tool grounded in students' own material.

## What "Working" Looks Like
In a one-minute demo, a student pastes real course material, chooses a topic, receives a relevant question based only on that material, answers it, and sees meaningful feedback with supporting evidence from the same material. Unsupported claims are not presented as evidence. The end-to-end chain should make the app's value clear on screen without requiring an explanation of a complicated technical system.

## The POC Boundary
Build the focused study loop: paste course text, choose a topic, generate one question based only on the supplied text, accept a free-form answer, and return a judgment (correct, partially correct, or needs improvement) with an explanation of included and missing points and evidence from the provided text. Do not rely on web searches or unrelated general knowledge to create questions or justify feedback, and do not present unsupported content as evidence. A fully offline system is not required; reliability of the complete end-to-end experience is the priority.

## Explicitly Cut
- User accounts and authentication.
- Dashboards and long-term progress tracking.
- Leaderboards and gamification systems.
- Social or community features.
- Large question banks.
- Automatic topic detection.
- File or document uploads; MVP input is pasted text.
- General-purpose chatbot features.
- Web search and external study resources.
