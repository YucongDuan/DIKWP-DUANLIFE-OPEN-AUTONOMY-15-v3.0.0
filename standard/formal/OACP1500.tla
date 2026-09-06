----------------------------- MODULE OACP1500 -----------------------------
EXTENDS Naturals, Sequences

CONSTANT MaxCycles
VARIABLES status, cycle, stopped, externalAuthority, protectedChanged, artifacts

Init ==
  /\ status = "active"
  /\ cycle = 0
  /\ stopped = FALSE
  /\ externalAuthority = 0
  /\ protectedChanged = FALSE
  /\ artifacts = 0

LocalAct ==
  /\ status = "active"
  /\ ~stopped
  /\ cycle < MaxCycles
  /\ cycle' = cycle + 1
  /\ artifacts' = artifacts + 1
  /\ UNCHANGED <<status, stopped, externalAuthority, protectedChanged>>

OwnerStop ==
  /\ stopped' = TRUE
  /\ status' = "paused"
  /\ UNCHANGED <<cycle, externalAuthority, protectedChanged, artifacts>>

Complete ==
  /\ status = "active"
  /\ artifacts >= 5
  /\ status' = "completed"
  /\ UNCHANGED <<cycle, stopped, externalAuthority, protectedChanged, artifacts>>

Next == LocalAct \/ OwnerStop \/ Complete

TypeOK ==
  /\ status \in {"active", "paused", "completed", "failed"}
  /\ cycle \in 0..MaxCycles
  /\ externalAuthority = 0
  /\ protectedChanged = FALSE

=============================================================================
