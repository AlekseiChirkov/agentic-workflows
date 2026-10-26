# Claude logging capabilities

hooks: yes
profile: claude-stop-v1
verified: 2026-10-25
runtime: Claude Code 2.1.309

The native Stop and SubagentStop mechanism is supported by this release. Isolated
native payload, correlation, ownership lifecycle and recovery fixtures provide
verification evidence; they do not demonstrate every workflow step in a live session.

Mechanism support, the current installation result, and accepted checkpoint coverage
are separate facts. A hook alone does not prove step coverage. A checkpoint needs
matching dispatch and report markers, one native Skill invocation and a producer
receipt. If capability is unknown or installation is unavailable, retain prompt
logging with `note: approximate`; unobserved boundaries also retain that path. Run start and run
end remain prompt driven. Uncertain delivery retries only its frozen correlated
payload and cannot claim a second logging route.

Installation requires Bash, Python 3.11 or newer, jq and flock. Python is used by the installer;
native hooks and ordinary logging retain their existing Bash/jq dependencies.
