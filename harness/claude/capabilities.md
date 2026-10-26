# Claude logging capabilities

hooks: yes
profile: claude-stop-v1
verified: 2026-10-25
runtime: Claude Code 2.1.309

The native Stop and SubagentStop mechanism is supported by this release. Isolated
native payload, correlation, ownership lifecycle and recovery fixtures provide
verification evidence; they do not demonstrate every workflow step in a live session.

Mechanism support, the current installation result, and accepted checkpoint coverage
are separate facts. A hook alone does not prove step coverage. Named workflow coverage
requires exactly one native Skill invocation, matching dispatch and report markers,
and a producer receipt. An unambiguously correlated session with no Skill invocation
may report `step: unknown`, providing observed coverage without named workflow coverage.
Unknown session coverage cannot suppress a named prompt event. A matching accepted
receipt for a named checkpoint suppresses only its corresponding prompt event.

If capability is unknown or installation is unavailable, retain prompt logging with
`note: approximate`; unobserved boundaries also retain that path. Run start and run
end remain prompt driven. Uncertain delivery retries only its frozen correlated
payload and cannot claim a second logging route.

Installation requires Bash, Python 3.11 or newer, jq and flock. Python is used by the
installer. Native hooks require Bash, jq and flock. Ordinary writes retain their existing
legacy dependencies, including optional jq.
