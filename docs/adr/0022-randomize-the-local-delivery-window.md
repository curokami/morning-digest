# ADR 0022: Randomize the local delivery window

## Decision

The production LaunchAgent starts `morning-digest-window` at 08:00 local time.
The launcher chooses a uniformly random second from the remaining time through
10:50 and waits before starting collection. If the Mac wakes after 08:00, the
choice is bounded by the remaining window. If it wakes or resumes after 10:50,
that day's run is skipped.

This removes the fixed daily request time without increasing request volume or
retry counts. Randomization is an operational precaution, not a claim that
Medium's protection policy is known or that random timing bypasses it.
