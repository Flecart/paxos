//! Generic Pedersen scheme in additive notation: m*G + r*H.
//! A backend must implement a prime-order group and canonical scalar field.
//! The caller supplies fresh uniform blinding; this library does not implement RNG,
//! parameter generation, curve arithmetic, encoding, or constant-time guarantees.

pub trait Group: Sized {
    type Scalar;
    fn scale(&self, scalar: &Self::Scalar) -> Self;
    fn add(&self, other: &Self) -> Self;
    fn same(&self, other: &Self) -> bool;
}

pub fn commit<G: Group>(g: &G, h: &G, message: &G::Scalar, blind: &G::Scalar) -> G {
    g.scale(message).add(&h.scale(blind))
}

pub fn verify<G: Group>(
    g: &G,
    h: &G,
    message: &G::Scalar,
    blind: &G::Scalar,
    commitment: &G,
) -> bool {
    commit(g, h, message, blind).same(commitment)
}

#[cfg(test)]
mod tests {
    use super::*;
    // Tiny, insecure group for an executable equation check only.
    struct Toy(u32);
    impl Group for Toy {
        type Scalar = u32;
        fn scale(&self, s: &u32) -> Self {
            Toy((self.0 * s) % 11)
        }
        fn add(&self, rhs: &Self) -> Self {
            Toy((self.0 + rhs.0) % 11)
        }
        fn same(&self, rhs: &Self) -> bool {
            self.0 == rhs.0
        }
    }
    #[test]
    fn opening_round_trip_and_rejection() {
        let c = commit(&Toy(1), &Toy(3), &4, &7);
        assert!(verify(&Toy(1), &Toy(3), &4, &7, &c));
        assert!(!verify(&Toy(1), &Toy(3), &5, &7, &c));
    }
}
