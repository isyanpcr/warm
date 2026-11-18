// Copyright 2024-2026 WritersLogic Contributors
// SPDX-License-Identifier: Apache-2.0
//! Encode a DNA read and a reference with `KmerEncoder` and score containment.
//! `cargo run --release --features experimental --example kmer_encoder`

// --8<-- [start:kmer]
use writerslogic_warm::core::kmer::{KmerConfig, KmerEncoder};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let encoder = KmerEncoder::new(KmerConfig {
        k: 15,
        dim: 1 << 20,
        ..KmerConfig::default()
    })?;
    let reference = encoder.encode(b"ACGTTGCAAGCTTGACCGTAGGCTAACGTTAGCCGATCGGATCAAGTC")?;
    let read = encoder.encode(b"acgttgcaagcttgaccguaggct")?; // case-insensitive; U is read as T
    let score = read.containment_similarity(&reference); // fraction of the read's bits in the reference
    println!("containment {score:.2}");
    Ok(())
}
// --8<-- [end:kmer]
