use serde::{Deserialize, Serialize};
use std::env;
use std::error::Error;
use std::fs::File;
use std::process;

// 1. TYPED STRUCT WITH OPTIONS
// We use Option<T> because CSV cells might be missing.
// serde will automatically map empty cells to `None`.
#[derive(Debug, Deserialize, Serialize)]
struct UserRecord {
    id: u32,
    name: Option<String>,
    age: Option<u8>,
    email: Option<String>,
}

fn main() {
    // Collect CLI arguments
    let args: Vec<String> = env::args().collect();

    // Basic syntax: Check if correct number of arguments are provided
    if args.len() < 3 {
        eprintln!("Usage: cargo run <input_csv> <output_json>");
        process::exit(1);
    }

    let input_path = &args[1];
    let output_path = &args[2];

    println!("Reading from {}...", input_path);

    // Call our processing function. If it returns an Err, we print it and exit.
    if let Err(e) = process_file(input_path, output_path) {
        eprintln!("Application error: {}", e);
        process::exit(1);
    }

    println!("Successfully wrote clean data to {}", output_path);
}

// 2. USING RESULT FOR FILE HANDLING
// The return type is Result<(), Box<dyn Error>>, which means it either 
// returns nothing `()` on success, or any type of Error on failure.
fn process_file(input_path: &str, output_path: &str) -> Result<(), Box<dyn Error>> {
    
    // Attempt to open the file. The `?` operator automatically returns an Error 
    // if the file is missing, avoiding a panic!
    let file = File::open(input_path)?;

    // Configure the CSV reader to trim messy whitespace from the tabular data
    let mut rdr = csv::ReaderBuilder::new()
        .trim(csv::Trim::All)
        .from_reader(file);

    let mut clean_records: Vec<UserRecord> = Vec::new();

    // Iterate through the CSV rows
    for result in rdr.deserialize() {
        match result {
            Ok(mut record) => {
                // 3. USING OPTION FOR MISSING CELLS
                // Sometimes a cell isn't totally empty, but has just spaces.
                // We want to turn empty strings into `None`.
                record.name = clean_string_option(record.name);
                record.email = clean_string_option(record.email);

                clean_records.push(record);
            }
            Err(e) => {
                // If a row violates our strict types (e.g., 'invalid_id' instead of u32),
                // we catch the error, log it, and skip the row instead of crashing.
                eprintln!("Warning: Skipping malformed row: {}", e);
            }
        }
    }

    // Create the output JSON file (again, ? handles file permission errors, etc.)
    let out_file = File::create(output_path)?;

    // Write the vector of structs to the file as pretty-printed JSON
    serde_json::to_writer_pretty(out_file, &clean_records)?;

    Ok(())
}

// Helper function to turn "" into None
fn clean_string_option(val: Option<String>) -> Option<String> {
    // `match` is the classic way to unwrap an Option safely
    match val {
        Some(s) if !s.is_empty() => Some(s),
        _ => None, // Returns None if it was already None, or if the string was empty
    }
}