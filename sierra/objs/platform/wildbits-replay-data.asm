* Replay records store resource operations for eventual save/restore.
* Private control state; the owner supplies a 510-byte record buffer.
replaylimit         rmb       1
replayused          rmb       2
replaycheckpoint    rmb       2
