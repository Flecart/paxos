//! Minimal reliable-delivery latch. The environment schedules delivery events.
pub fn step(state: u8, deliver: bool) -> u8 {
    if deliver {
        1
    } else {
        state
    }
}
